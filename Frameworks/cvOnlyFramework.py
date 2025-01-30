# This code is based off Evan Juras's TFLite implementation for Android and Raspberry pi at:
# https://github.com/EdjeElectronics/TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi/blob/master/deploy_guides/Raspberry_Pi_Guide.md


# Import packages
import os
import cv2
import numpy as np
import sys
import detector
import time


class ANDRRFramework:
    '''Framework for displaying CV detections over RCA'''
    def __init__(self):
        
        self.CVModel='edgetpu.tflite' #File name of cv model
        self.useTPU=True #Set to true if using ML accelerator
        self.DEBUG=True #If true, the display window isn't full screen to help with reading the terminal
        self.imW=800 #Display image resolution width
        self.imH=450 #Display image resolution height
        self.CamW=800 #Camera resolution width
        self.CamH=600 #Camera resolution height
        self.folderName="radioImages0/" #Stores what folder data is saved to
        self.cameraIndex=1

        self.cap=cv2.VideoCapture(self.cameraIndex, cv2.CAP_V4L2)
        ret = self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.cap.set(3,self.CamW)
        ret = self.cap.set(4,self.CamH)

        self.detector=detector.CVProcessor(self.CVModel,self.useTPU,self.imW,self.imH)

    def processImage(self): #Run an image through the CV program, add the relevant data, save the image
        while True:
            ret, image=self.cap.read()
            image=cv2.resize(image,(self.imW,self.imH))

            if ret:
                #Run the dector program, and save the resulting image and data
                frame,cvData = self.detector.detect(image) #Run the image through the detector program
                #Display image
                #If not using debug mode, set image to full screen 
                if not ANDRR.DEBUG:
                    cv2.setWindowProperty('radioImage', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                #Show image
                cv2.imshow('radioImage', frame)
                if cv2.waitKey(1) == ord('q'):
                    break 

    
#Initialize the framework
ANDRR=ANDRRFramework()
time.sleep(1)

#Setup display window
cv2.namedWindow('radioImage', cv2.WINDOW_NORMAL)

ANDRR.processImage()