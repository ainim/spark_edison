#!/usr/bin/env python

import mraa
import time
import pulsein
import database
import os
from  multiprocessing import Value, Process, Lock
from datetime import datetime

NODE=1
DELTAT_ULTRA = 0.2
#ALERT_FLAG = 0
MAX_WATER = 20 # in centimeters
PLUVIOMETER = 1
ULTRASONIC = 2 

class Sensor:
    "Defines Sensor attributes and methods"

    def __init__(self, type = '' , unit = '' , conv_ratio = 1 ,  
                 file = '', timeint = 60, status = 1) :
        self.type = type
        self.unit = unit
        self.conv_ratio = conv_ratio
        self.file = file 
        self.timeint = timeint
        self.status = status
    def thread(self, args):
        return 
    def __init__gpio(self):
        return
    def thread_write(self, args):
        return


class Pluviometer(Sensor):
    "Defines methods to read from pluviometer"
    
    def __init__gpio(self, gpio_pin, gpio_dir):
        self.gpio = mraa.Gpio(gpio_pin)
        self.gpio.dir(gpio_dir)
        self.gpio.mode(mraa.MODE_PULLUP)

    def __init__(self, type = 'pluviometer' , unit = 'mm' , conv_ratio = 1 ,
                 file = 'measurement', timeint = 2, status = 1, gpio_pin = 4,
                 gpio_dir = mraa.DIR_IN) : 
        Sensor.__init__(self, type, unit, conv_ratio, file,timeint, status) 
        self.__init__gpio(gpio_pin, gpio_dir)

    def thread(self, args):
        print 'Hello from thread_pluv'
        self.gpio.isr(mraa.EDGE_BOTH, pluviometer_interrupt,
                      pluviometer_interrupt)
        while True:
            time.sleep(1)

    def thread_write(self, args):
        print 'time: {}'.format( self.timeint)
        while True:
            lcounter = pluviometer_value.value
            with pluviometer_lock:
                print "write: unlocked"
                #pluviometer_value.value = 0
            measure = lcounter * self.conv_ratio
            print "write: {0}, {1} mm".format(lcounter, measure)
            if self.file <> '' : 
                with open(self.file, 'a') as file :
                    with measurement_lock:
                        file.write('{0},{1},{2},{3}\n'.format(NODE, datetime.now(), measure, self.type))
            time.sleep(self.timeint)

# Pluviometer Global definitions

pluviometer_value= Value('i',0)
pluviometer_lock = Lock()
measurement_lock = Lock()

def pluviometer_interrupt(args):
    print 'Touched!!!'
    with pluviometer_lock:
        pluviometer_value.value += 1
    print "interrupt: {0}".format(pluviometer_value.value)

class Ultrasonic(Sensor) :
    "Defines methods to read from ultrasonic sensor"

    def __init__gpio(self, echo_pin, trigger_pin):
        self.echo_pin=mraa.Gpio(echo_pin)
        self.trigger_pin = mraa.Gpio(trigger_pin)
        self.echo_pin.dir(mraa.DIR_IN)
        self.trigger_pin.dir(mraa.DIR_OUT)

    def __init__(self, type = 'ultrasonic' , unit = 'cm' , conv_ratio = 58.2 ,
                 file = 'measurement', timeint = 1, status = 1, echo_pin = 6,
                 trigger_pin = 5, max_range = 400, min_range = 0, initial_value=46.5):
        Sensor.__init__(self, type,unit,conv_ratio,file,timeint, status)
        self.__init__gpio(echo_pin, trigger_pin)
        self.max_range = max_range
        self.min_range = min_range
        self.initial_value = initial_value

    def thread(self, args):
        ALERT_FLAG = 0
        while True: 
            self.trigger_pin.write(0)
            time.sleep(0.000002) #2 microseconds
            self.trigger_pin.write(1)
            time.sleep(0.00001)  #10 microseconds
            self.trigger_pin.write(0)
            duration  = pulsein.pulseIn(self.echo_pin) # microseconds 
            ultrasonic_value.value = self.initial_value - (duration / self.conv_ratio) # distance
            
            if ultrasonic_value.value >= MAX_WATER :
                if ALERT_FLAG == 0:
                    ALERT_FLAG = 1
                    print 'ALERT UP!!!!!!!!!'
                    database.insertAlert(datetime.now(), NODE, ALERT_FLAG)
            else :
                if ALERT_FLAG == 1:
                    ALERT_FLAG = 0
                    print 'ALERT DOWM!!!!!!!'
                    database.insertAlert(datetime.now(), NODE ,ALERT_FLAG)

            if ultrasonic_value.value >= self.max_range or \
                ultrasonic_value.value <= self.min_range :
                print "Out of range {0}".format(ultrasonic_value.value)
                ultrasonic_value.value = -1
            else :
                print "Distance: {0} cm".format(ultrasonic_value.value)
            time.sleep(DELTAT_ULTRA)

    def thread_write(self, args):
        print 'time: {}'.format( self.timeint)
        while True:
            print "write:"
            if self.file <> '' :
                with measurement_lock:
                    with open(self.file, 'a') as file :
                        file.write('{0},{1},{2},{3}\n'.format(NODE, datetime.now(), ultrasonic_value.value, self.type))
            time.sleep(self.timeint)
               
ultrasonic_value = Value('d',0.0)

def write_to_db(file,timeint):
    while True :
        # Read input file
        with measurement_lock:
            with open(file, 'r') as f :
                registers = f.readlines()
            if os.path.isfile(file):
                try: 
                    os.remove(file) 
                except OSError as e: 
                    print '================== Cannot remove {0} file, err {1}'.format(file,e)
                    continue
        print '================= Sending to DB'
        for reg in registers:
            fields = reg.split(',')
            database.insertMeas(fields)
        time.sleep(timeint)
 
        
if __name__ == '__main__':
    meas_file = 'measurement'
    pluviometer = Pluviometer(PLUVIOMETER,'mm',1,meas_file, 2.0) 
    pluviometer_thread = Process(target=pluviometer.thread, args=(None,))
    pluviometer_write = Process (target=pluviometer.thread_write, 
                                 args=(None,))
    ultrasonic = Ultrasonic(ULTRASONIC,'cm', 58.2, meas_file, 1.0)
    ultrasonic_thread = Process(target = ultrasonic.thread, args=(None,))
    ultrasonic_write = Process(target = ultrasonic.thread_write, args=(None,))
    measurement_db = Process(target = write_to_db, args=(meas_file,20))
    measurement_db.start()
    ultrasonic_thread.start()
    ultrasonic_write.start()
    pluviometer_thread.start()
    pluviometer_write.start()

    try: 
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print "Good Bye! :)"
        pluviometer_thread.terminate()
        pluviometer_write.terminate()
        ultrasonic_thread.terminate()
        ultrasonic_write.terminate()
        measurement_db.terminate()
