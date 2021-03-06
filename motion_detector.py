#! /usr/bin/env python3
#
# Code to control motion sensor that activates audio



##########################################################################################################
#                           GENERAL SETUP                                                                #
##########################################################################################################

import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import time
import subprocess
import threading
import logging
import numpy as np

def setup():
    GPIO.setmode(GPIO.BOARD)
    
def cleanup():
    GPIO.cleanup()

    


##########################################################################################################
#                           BUTTON CONTROL  THREAD                                                       #
##########################################################################################################

class ButtonThread(threading.Thread):
    
    def __init__(self, button_num):
        super().__init__()
        
        logging.info("initializing button thread")
        
        self.button_num = button_num
        self._status = 0
        self._locked = False
        
        # GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.button_num, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def reset_status(self):
        self._status = 0
        
    def get_status(self):
        return self._status
        
    def run(self):
        
        logging.debug("starting button thread")
        
        try:
            while True:
                if not self._locked:
                    GPIO.wait_for_edge(self.button_num, GPIO.FALLING)
                    
                    start = time.time()
                    time.sleep(0.2) #allowing voltage to drop
                
                    while GPIO.input(self.button_num) == GPIO.LOW: #waiting for button release
                        time.sleep(0.01)
                        
                    buttonTime = time.time() - start #getting button press duration
                    
                    
                    if buttonTime >= 6: #power off
                        self._status = 3
                        logging.debug("button status 3 (poweroff)")
                    elif buttonTime >= 3: #deactivate
                        self._status = 2
                        logging.debug("button status 2 (deactivate)")
                    elif buttonTime >= .3: #activate/reactivate
                        self._status = 1
                        logging.debug("button status 1 (reactivate)")
                        
                        
        except KeyboardInterrupt:    
            cleanup()

            
            
            
            
            
##########################################################################################################
#                               LED CONTROL THREAD                                                       #
##########################################################################################################




class LED_Thread(threading.Thread):
    
    def __init__(self, ledPin):
        super().__init__()
        
        logging.info("initializing LED thread")
        
        self.ledPin = ledPin
        self.set_mode(1) #initializes blinking as in pre-activation period
        
        # GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.ledPin, GPIO.OUT)
        
        self.current_status = 0 #0 for low, 1 for high
        GPIO.output(self.ledPin, GPIO.LOW)
        self.last_switch = datetime.utcnow()
        
    def get_mode(self):
        return self._mode
        
    def set_mode(self,mode):
        logging.debug(f"setting LED mode to {mode}")
        self._mode = mode
        if mode == 0: #deactivated - system doesn't blink (blinkrate var not used)
            self.blinkrate == 1E12
        elif mode == 1: #mode 1 = waiting for initial activation
            self.blinkrate = 0.1 #blink at 5 Hz (change status every 0.1 sec)
        elif mode == 2: #mode 2 = active system
            self.blinkrate = 0.5 #blink at 1 Hz (change status every 0.5 sec)
        elif mode == 3: #mode 3 = in delay between activations
            self.blinkrate = 1 #blink at 0.5 Hz (change status every 1 sec)
            
            
    def set_on(self):
        GPIO.output(self.ledPin,GPIO.HIGH)
            
    #unique blink pattern to acknowledge shutdown
    def acknowledge_blink(self):
        cmode = self._mode
        self.set_mode(0) #deactivate LED
        time.sleep(0.25)
        for i in range(5):
            if i != 3:
                GPIO.output(self.ledPin,GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(self.ledPin,GPIO.LOW)
            time.sleep(0.2)
        self.set_mode(cmode)
        
    def switch_light(self):
        # logging.info("switching LED")
        if self.current_status == 0:
            GPIO.output(self.ledPin, GPIO.HIGH)
            self.current_status = 1
        else:
            GPIO.output(self.ledPin, GPIO.LOW)
            self.current_status = 0
        self.last_switch = datetime.utcnow()
            
        
    def run(self):
        logging.debug("starting LED thread")
        try:
            while True:
                if self._mode == 0:
                    GPIO.output(self.ledPin, GPIO.LOW)
                elif (datetime.utcnow() - self.last_switch).total_seconds() >= self.blinkrate:
                    self.switch_light()
                        
                time.sleep(0.05) 
                
        except KeyboardInterrupt:    
            cleanup()
            





    
    

##########################################################################################################
#                           MOTION DETECTOR THREAD                                                       #
##########################################################################################################
    
class MotionThread(threading.Thread):
    
    def __init__(self, echoPin, trigPin, distThresh, Nobs, initial_delay, refresh_activation_limit):
        
        logging.info("initializing motion thread")
        
        super().__init__()
        # GPIO.setmode(GPIO.BOARD)
        self.echoPin = echoPin
        self.trigPin = trigPin
        
        GPIO.setup(self.echoPin, GPIO.IN)
        GPIO.setup(self.trigPin, GPIO.OUT)
        
        GPIO.output(self.trigPin, GPIO.LOW) #set trigger pin LOW
        
        self._range_values = []
        self.Nobs = Nobs #number of obs to determine mean in list
        
        self.distThresh = distThresh #distance change threshold (cm) to detect motion
        
        self.refresh_activation_limit = refresh_activation_limit*60 #time (minutes) required between sensor triggers 
        
        self._activated = False
        self.set_activation_time(initial_delay)
        
        self._range = np.NaN
    
        
        
    #adjusts when the motion sensor thinks it last activated so it can't activate the first time until the specified initial delay (minutes) has passed
    def set_activation_time(self,initial_delay):
        self._last_activated = datetime.utcnow() - timedelta(seconds = (self.refresh_activation_limit - initial_delay*60)) 
        self.delay_status = 1 #changes to 1 when activated and 2 when in post-activation delay
        
    def get_status(self):
        return self._activated
        
        
    def deactivate(self): #for parent thread to deactivate motion trigger after acknowledging it
        self._activated = False
        
    
    def return_current_range(self): #callable method to retrieve last measured range
        return self._range, self._range_values
        
        
    #retrieve a single range measurement from ultrasonic sensor
    def get_range(self):
        
        #send signal through trigger pin for 10 microseconds
        GPIO.output(self.trigPin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trigPin, GPIO.LOW)
        
        #wait for echo signal to start
        while GPIO.input(self.echoPin) == GPIO.LOW:
            start = time.time() #constantly update start time, last value right before echoPin goes high
            
        #wait for echo signal to finish
        while GPIO.input(self.echoPin) == GPIO.HIGH:
            finish = time.time() #constantly update finish time, last value right before echoPin goes low
        
        pulselen = finish - start #total pulse length (corresponds to round trip time for sound)
        
        #speed of sound = 343 m/s
        #distance (m) = time (s) * sound speed
        #distance (cm) = time (s) / 2 (two way trip) * 100 (m -> cm); 343*100/2
        distance_cm = np.round(17150.0 * pulselen, 1) #round to nearest mm (error is 3 mm anyways)
        
        if distance_cm > 100: #setting max range to 1 m
            distance_cm = 200
        
        return distance_cm
        
        
    def check_range_diff(self):
        detected = False
        self._range = self.get_range()
        
        #triggers motion detector when range on sensor differs from observed range by measured amount
        if np.abs(self._range - np.nanmean(np.asarray(self._range_values))) >= self.distThresh:
            detected = True
            
        self._range_values.append(self._range) #adding new ob to range calculations for future iterations
        
        #keeping list to specified length if necessary
        if len(self._range_values) > self.Nobs:
            self._range_values.pop(0) #drop the first (oldest) observation
        
        return detected
        
        
            
    def run(self):
        logging.debug("starting motion thread")
        try:
            
            while True:
                
                #to set self.activated = True (which triggers audio in the main thread):
                # the distance must differ from mean 5 previous values by greater than the threshold
                # the previous activation must be outside the time limit assigned when initializing the thread
                
                #this function is called regardless of whether the system is "active" because it needs to 
                #keep getting observations to create an accurate mean distance
                detected = self.check_range_diff()
                
                #checking if activation delay is passed
                if not self._activated and (datetime.utcnow() - self._last_activated).total_seconds() >= self.refresh_activation_limit:
                    self.delay_status = 2
                    
                    #checking 
                    if detected:
                        logging.debug("motion detected")
                        self._activated = True
                        self._last_activated = datetime.utcnow()
                        self.delay_status = 3
                                    
                time.sleep(0.2) # would be 5 Hz if not for time to calculate range
                
        except KeyboardInterrupt:
            cleanup()
            

            
            
            
            
            
##########################################################################################################
#                           AUDIO PLAYER THREAD                                                          #
##########################################################################################################
class AudioThread(threading.Thread):
    
    # import pygame
    
    def __init__(self,audio_file):
        logging.info("initializing audio thread")
        super().__init__()
        self._is_playing = False
        self.request_play = False
        self.audio_file = audio_file
        self.audio_command = "aplay -D hw:0,0 /home/pi/MotionDetector/soundsource.wav" #command to play audio file
        
        #setting volume to 85%
        cmd = "sudo amixer cset numid=1 85%" 
        subprocess.run(cmd.split())
        
        
    #call from parent thread when it is time to play the audio
    def request_play_audio(self):
        logging.debug(f"requesting to play audio (_is_playing = {self._is_playing}")
        if not self._is_playing:
            self._is_playing = True
            self.request_play = True
    
         
    #constantly running loop monitoring to play audio   
    def run(self):
        logging.debug("starting audio thread")
        while True:
            if self.request_play:
                self._is_playing = True
                self.request_play = False
                self.play_audio()
                self._is_playing = False
            
            time.sleep(0.2) 
                
            
    #play audio (WAV file) with pygame
    def play_audio(self):
        logging.debug("playing audio")
        # self.pygame.mixer.init()
        # self.pygame.mixer.music.load(self.audio_file)
        # self.pygame.mixer.music.play()
        # while self.pygame.mixer.music.get_busy() == True:
        #     time.sleep(0.1)
        subprocess.run(self.audio_command.split())
        
            
            
            
            
            
            
##########################################################################################################
#                           MAIN EVENT LOOP                                                              #
##########################################################################################################

if __name__ == "__main__":
    
    logging.basicConfig(filename=f'motion_detector_{datetime.utcnow():%Y%m%d_%H%M}.log', level=logging.DEBUG)
    setup() #using BOARD pin numbers (not BCM)
    
    #initiating button monitor
    buttonPin = 10 #connect button gpio to 10 and button ground to 9
    buttonMonitor = ButtonThread(button_num=buttonPin)
    buttonMonitor.start()
    #modes = 1: activated, 2: deactivated, 3: off, 0: no new info
    
    #initiating LED device thread
    ledPin = 16
    ledMonitor = LED_Thread(ledPin=ledPin)
    ledMonitor.set_on() #initally just on while device starting up
    #modes: 1=initial activation delay (5 Hz), 2 = activated (1 Hz), 3 = between activations (0.5Hz), 0 = deactivated (off)
        
    #starting LED monitor (sets mode 1)
    ledMonitor.start()
    
    #initiating motion sensor
    echoPin = 35 #returns echo time
    trigPin = 36 #triggers range detector observation
    distThresh = 10 #distance change in cm to trigger motion detector
    motionThread = MotionThread(echoPin=echoPin, trigPin=trigPin, distThresh=distThresh, Nobs=20, initial_delay=0.5, refresh_activation_limit=10)
    motionThread.start()
    
    #initiating audio thread
    audioFile = "soundsource.wav" 
    audioThread = AudioThread(audio_file = audioFile)
    audioThread.start()
    
    
    
    
    systemActive = True #whether or not system is active
    
    #main event loop, keeping track of button presses, motion sensing and triggering audio to play
    try:
    
        while True:
            if systemActive and motionThread.get_status():
                audioThread.request_play_audio()
            motionThread.deactivate()
            
            buttonStatus = buttonMonitor.get_status()
            if buttonStatus == 3:
                logging.info("Shutting down")
                ledMonitor.acknowledge_blink() #blink to acknowledge poweroff command
                cmd = "sudo shutdown -h now" #power off Pi
                subprocess.run(cmd.split())
                
            elif buttonStatus == 2:
                logging.info("Deactivating")
                systemActive = False #deactivate motion sensor
                
            elif buttonStatus == 1:
                logging.info("Reactivating")
                motionThread.set_activation_time(0.25) #will wait 15 sec to activate
                motionThread.deactivate()
                systemActive = True
                
            buttonMonitor.reset_status()
                
            if not systemActive:
                desiredLEDmode = 0
            else:
                desiredLEDmode = motionThread.delay_status
                
            #switching LED mode if necessary
            if desiredLEDmode != ledMonitor.get_mode():
                ledMonitor.set_mode(desiredLEDmode)
            time.sleep(0.1)
            
        
    except KeyboardInterrupt:
        cleanup()
        
        
        
        
        
        
        