import os
import datetime
import serial


class SERIAL_COMM:
   def __init__(self, serial_port='COM5', baudrate=19200, log_file='../serial_log-110920-130920.txt'):
      self.serial = serial.Serial(serial_port, baudrate, timeout=0)
      self.logfile = log_file
      if os.path.exists(self.logfile):
         os.remove(self.logfile)
      pass

   def log(self):
      data = self.serial.readline().decode('ascii').rstrip('\r\n')
      if data:
         with open(self.logfile, 'a') as logfile:
            string_to_log = str(datetime.datetime.now()) + " ::::: " + data + '\n'
            print(string_to_log, end='')
            logfile.write(string_to_log)
         pass
      pass
   pass