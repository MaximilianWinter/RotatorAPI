# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 16:25:15 2021

@author: mWinter 
winter.maximilian (at) physik.lmu.de

Simple API for the Thorlabs ELL14 Elliptec rotation stage.
"""
import serial
import time
import struct

class RotatorDevice():
    
    default_commands = {'info'              : ('in', 0, 'IN', 30),
                        'get_position'      : ('gp', 0, 'PO', 8),
                        'get_home_offset'   : ('go', 0, 'HO', 8),
                        'get_jogstep_size'  : ('gj', 0, 'GJ', 8),
                        
                        'move_to_home_cw'   : ('ho0', 0, 'PO', 8),
                        'move_to_home_ccw'  : ('ho1', 0, 'PO', 8),
                        'move_absolute'     : ('ma', 8, 'PO', 8),
                        'move_relative'     : ('mr', 8, 'PO', 8),
                        'move_forward'      : ('fw', 0, 'PO', 8),
                        'move_backward'     : ('bw', 0, 'PO', 8),
                        'set_jogstep_size'  : ('sj', 8, 'GJ', 8)}
    
    def __init__(self, serial, address=0, commands = default_commands, rev_in_pulses = 143360):
        """
        serial: running serial instance
        
        address: int (0-8), internal address of device
        
        commands: dict, of all available commands, structured as {key: ('command', n_write, 'reply', n_read)},
                    where n_write is the number of bytes to be written, and n_read the number of bytes to be read
                    with the respective command
                    
        rev_in_pulses: one full revolution (2pi = 360 degrees) in pulses
        """
        self.ser = serial
        self.address = str(address)
        
        self.commands = commands
        
        self.ser.flushInput()
        self.ser.write(bytes(self.address + 'in', 'ascii'))
        time.sleep(0.1)
        self.device_info = self.ser.readline()
        
        self.rev_in_pulses = rev_in_pulses
        
    def write(self, key,  val_deg = None, read=True):
        """
        key: string, one of the available keys in the commands dict
        
        val_deg: float, int or None, value in degrees
        
        returns: tuple of bytes (command string), int (reply in pulses), float (reply in deg) or None
        
        """
        # value must be in degrees
        if key in self.commands.keys():
            command, n_write, reply, n_read = self.commands[key]
            
            if isinstance(val_deg,(int,float)): # must be 4 bytes
                val_pulses = self.degree_to_pulses(val_deg)
                
                byte_string = bytes(self.address + command + val_pulses, 'ascii') 
            else:
                byte_string = bytes(self.address + command, 'ascii')
                
            if read == True:
                self.ser.flushInput()
            self.ser.write(byte_string)
            
            if read == True:            
                line = self.ser.readline()

                while (line[0:3] == bytes(self.address + 'GS', 'ascii')) or (line[0:3] == bytes(self.address + reply, 'ascii')):
                    
                    if line[0:3] == bytes(self.address + reply, 'ascii'):
                        val_pulses_hex = (8-n_read)*'0' + line[3:n_read+3].decode()
                        
                        return byte_string, self.hex_to_decimal(val_pulses_hex), self.pulses_to_degrees(val_pulses_hex)
                    
                    line = self.ser.readline()

            return byte_string, None, None
        else:
            return None, None, None
        
    def degree_to_pulses(self, val_degree):
        """
        val_degree: float or int (4 bytes)
        
        returns: bytes, converted value to pulses in hexadecimal and byte format
        """
        return struct.pack('>l', int(val_degree*self.rev_in_pulses/360)).hex().upper()
        
        
        
    def pulses_to_degrees(self, val_pulses):
        """
        val_pulses: string, corresponding to a 4 byte hexadecimal number
        
        returns: float (4 byte), converted value to degrees 
        """
        return 360*struct.unpack('>l', bytes.fromhex(val_pulses))[0]/self.rev_in_pulses
    
    def hex_to_decimal(self, val_hex):
        """
        val_hex: string, corresponding to a 4 byte hexadecimal number
        
        returns: long int (4 bytes) 
        """
        return struct.unpack('>l', bytes.fromhex(val_hex))[0]
        

class RotatorAPI():
    
    def __init__(self, port='COM3', n_devices=1):
        
        self.ser = serial.Serial('COM3', baudrate=9600, timeout=2)
        
        self.dev = {}
        
        for i in range(n_devices):
            self.dev[i] = RotatorDevice(self.ser, address=i)
            
        #locals().update(self.devices)
    def __del__(self):
        self.ser.close()
        
    def close(self):
        self.ser.close()
        
        