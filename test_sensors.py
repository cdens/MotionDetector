#! /usr/bin/env python3
# code to test the IR motion detector or ultrasonic range detector and supporting code

import time
import RPi.GPIO as GPIO
import numpy as np
import traceback

def test_audio_range(echoPin, trigPin):
    
    from motion_detector import MotionThread
    
    distThresh = 5 #distance change threshold for motion detection in cm
    motionThread = MotionThread(echoPin=echoPin, trigPin=trigPin, distThresh=distThresh, Nobs=20, initial_delay=0.1, refresh_activation_limit=0)
    motionThread.start()
    
    print("Warming up (10 sec)")
    time.sleep(10) #give thread a chance to finish initializing 
    
    # print motion detection stats in constant loop
    while True:
        
        #get info
        crange, rangevals = motionThread.return_current_range()
        isActive = motionThread.get_status()
        motionThread.deactivate()
        
        print(f"Range: {crange} cm, Motion: {isActive} (Mean: {np.round(np.nanmean(np.asarray(rangevals)),1)} cm)")
        time.sleep(0.5)
        
    
    
    
    
    
    
def test_IR_motion(motionPin):
    
    from motion_detector_IR import MotionThread_IR
    
    #initiating motion sensor
    motionThread_IR = MotionThread_IR(pin=motionPin, initial_delay=0.1, refresh_activation_limit=0) #no refresh
    motionThread_IR.start()
    
    print("Warming up (10 sec)")
    time.sleep(10) #give thread a chance to finish initializing 
    
    # print motion detection stats in constant loop
    while True:
        isActive = motionThread_IR.get_status()
        motionThread_IR.deactivate()
        print(f"IR motion status: {isActive}")
        time.sleep(0.5)
    
    
    
    
if __name__ == "__main__":
    
    GPIO.setmode(GPIO.BOARD)
    
    
    try:
        # IR MOTION DETECTOR
        # motionPin = 12
        #test_IR_motion(motionPin)
        
        # AUDIO RANGE MOTION DETECTOR
        echoPin = 35 
        trigPin = 36 
        test_audio_range(echoPin, trigPin)
        
    except Exception as e:
        GPIO.cleanup()
        traceback.print_exc()