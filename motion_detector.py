#! /usr/bin/env python3
#
# Code to control motion sensor that activates audio



##########################################################################################################
#                           GENERAL SETUP                                                                #
##########################################################################################################

import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import time
import pygame #for audio
import subprocess


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
        
        self.button_num = button_num
        self._status = 0
        self._locked = False
        
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.button_num, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def reset_status(self,status):
        self._status = 0
        
    def get_status(self):
        return self._status
        
    def run(self):
        
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
                    elif buttonTime >= 3: #deactivate
                        self._status = 2
                    elif buttonTime >= .3: #activate/reactivate
                        self._status = 1
                        
                        
        except KeyboardInterrupt:    
            cleanup()

            
            
            
            
            
##########################################################################################################
#                               LED CONTROL THREAD                                                       #
##########################################################################################################




class LED_Thread(threading.Thread):
    
    def __init__(self, ledPin):
        super().__init__()
        
        self.ledPin = ledPin
        self._mode = 1 #initializes blinking as in pre-activation period
        
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.ledPin, GPIO.OUT)
        
        self.current_status = 0 #0 for low, 1 for high
        GPIO.output(self.ledPin, GPIO.LOW)
        self.last_switch = datetime.utcnow()
        
        
    def set_mode(self,mode):
        self._mode = mode
        if mode == 0: #deactivated - system doesn't blink (blinkrate var not used)
            self.blinkrate == 1E12
        elif mode == 1: #mode 1 = waiting for initial activation
            self.blinkrate = 0.1 #blink at 5 Hz (change status every 0.1 sec)
        elif mode == 2: #mode 2 = active system
            self.blinkrate = 0.5 #blink at 1 Hz (change status every 0.5 sec)
        elif mode == 3: #mode 3 = in delay between activations
            self.blinkrate = 1 #blink at 0.5 Hz (change status every 1 sec)
        
    def switch_light(self):
        if self.current_status = 0:
            GPIO.output(self.ledPin, GPIO.HIGH)
            self.current_status = 1
        else:
            GPIO.output(self.ledPin, GPIO.LOW)
            self.current_status = 0
        self.last_switch = datetime.utcnow()
            
        
    def run(self):
        
        try:
            while True:
                if (self.last_switch - datetime.utcnow()).total_seconds >= self.blinkrate:
                    self.switch_light()
                        
                time.sleep(0.05) 
                
        except KeyboardInterrupt:    
            cleanup()
            





    
    

##########################################################################################################
#                           MOTION DETECTOR THREAD                                                       #
##########################################################################################################
    
class MotionThread(threading.Thread):
    
    def __init__(self,pin,initial_delay, refresh_activation_limit):
        
        super().__init__()
        GPIO.setmode(GPIO.BOARD)
        self.pin = motionPin
        GPIO.setup(self.pin, GPIO.IN)
        
        self._activated = False
        self.set_activation_time(initial_delay)
        
        self.refresh_activation_limit = refresh_activation_limit*60 #time (minutes) required between sensor triggers 
    
        
        
    #adjusts when the motion sensor thinks it last activated so it can't activate the first time until the specified initial delay (minutes) has passed
    def set_activation_time(self,initial_delay)
        self._last_activated = datetime.utcnow() - timedelta(seconds = (self.refresh_activation_limit - initial_delay*60)) 
        self.delay_status = 1 #changes to 1 when activated and 2 when in post-activation delay
        
    def get_status(self):
        return self._activated
        
        
    def deactivate(self): #for parent thread to deactivate motion trigger after acknowledging it
        self._activated = False
        
            
    def run(self):
        
        try:
            oldPinStatus = True
            
            while True:
                newPinStatus = GPIO.input(motionPin) == GPIO.HIGH
                
                #to set self.activated = True (which triggers audio in the main thread):
                # the pin must switch from LOW to HIGH (we don't care about HIGH to LOW)
                # activated must have not already been set
                # the previous activation must be outside the time limit assigned when initializing the thread
                
                #checking if activation delay is passed
                if not self._activated and (datetime.utcnow() - self._last_activated).total_seconds() >= self.refresh_activation_limit:
                    self.delay_status = 2
                    
                    #checking 
                    if not oldPinStatus and newPinStatus:
                        self._activated = True
                        self._last_activated = datetime.utcnow()
                        self.delay_status = 3
                    
                oldPinStatus = newPinStatus
                    
                sleep(0.5) #2 Hz refresh rate
                
        except KeyboardInterrupt:
            cleanup()
            

            
            
            
            
            
##########################################################################################################
#                           AUDIO PLAYER THREAD                                                          #
##########################################################################################################
class AudioThread(threading.Thread):
    
    def __init__(self,audio_file):
        
        super().__init__()
        self._is_playing = False
        self.request_play = False
        self.audio_file = audio_file
        
        
    #call from parent thread when it is time to play the audio
    def request_play_audio(self):
        if not self._is_playing:
            self._is_playing = True
            self.request_play = True
    
         
    #constantly running loop monitoring to play audio   
    def run(self):
        while True:
            if self.request_play:
                self._is_playing = True
                self.request_play = False
                self.play_audio()
                self._is_playing = False
            
            time.sleep(0.2) 
                
            
    #play audio (WAV file) with pygame
    def play_audio(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() == True:
            time.sleep(0.1)
            
        
            
            
            
            
            
            
##########################################################################################################
#                           MAIN EVENT LOOP                                                              #
##########################################################################################################

if __name__ == "__main__":
    
    
    setup() #using BOARD pin numbers (not BCM)
    
    #initiating motion sensor
    motionPin = 12
    motionThread = MotionThread(pin=motionPin, initial_delay=2, refresh_activation_rate=10) #refresh = 10 minutes
    motionThread.start()
    
    #initiating audio thread
    audioFile = "soundsource.wav" 
    audioThread = AudioThread(audio_file = audioFile)
    audioThread.start()
    
    #initiating button monitor
    buttonPin = 10 #connect button gpio to 10 and button ground to 9
    buttonMonitor = ButtonThread(button_num=buttonPin)
    buttonMonitor.start()
    #modes = 1: activated, 2: deactivated, 3: off, 0: no new info
    
    #initiating LED device thread
    ledPin = 16
    ledMonitor = LED_Thread(ledPin=ledPin)
    ledMonitor.start()
    ledMonitor.set_mode(1) 
    #modes: 1=initial activation delay (5 Hz), 2 = activated (1 Hz), 3 = between activations (0.5Hz), 0 = deactivated (off)
    
    
    systemActive = True #whether or not system is active
    
    #main event loop, keeping track of button presses, motion sensing and triggering audio to play
    try:
    
        while True:
            if systemActive and motionThread.getStatus():
                motionThread.deactivate()
                audioThread.request_play_audio()
            
            buttonStatus = buttonMonitor.get_status()
            if buttonStatus == 3:
                cmd = "sudo shutdown -h now" #power off Pi
                subprocess.run(cmd.split())
                
            elif buttonStatus == 2:
                systemActive = False #deactivate motion sensor
                
            elif buttonStatus == 1:
                motionThread.set_activation_time(1) #will wait 1 min to activate
                motionThread.deactivate()
                systemActive = True
                
            if not systemActive:
                ledMonitor.set_mode(0)
            else:
                ledMonitor.set_mode(motionThread.delay_status)
                            
            time.sleep(0.1)
            
        
    except KeyboardInterrupt:
        cleanup()
        
        
        
        
        
        
        