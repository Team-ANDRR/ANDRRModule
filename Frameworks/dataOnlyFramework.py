# This code is based off Evan Juras's TFLite implementation for Android and Raspberry pi at:
# https://github.com/EdjeElectronics/TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi/blob/master/deploy_guides/Raspberry_Pi_Guide.md


# Import packages
import os
import cv2
import numpy as np
import sys
import time
import csv
import serial
import detector
from multiprocessing import Process,Queue
from pymavlink import mavutil

class ANDRRFramework:
    '''Framework for displaying CV detections over RCA'''
    def __init__(self):
        
        self.newFolder=False #If true, a new folder will be created to save images and image data to
        self.DEBUG=True #If true, the display window isn't full screen to help with reading the terminal
        self.addImageLabel=True #If true, the program will add a label with ID and timestamp data to the bottom of all images
        self.saveImage=False #If true, processed images will be saved to the pi
        self.saveData=True #If true, data from the detection program will be saved to a csv file
        self.showImage=True #If true, images will be displayed on screen
        self.imW=800 #Image resolution width
        self.imH=450 #Image resolution height
        self.serOut='/dev/ttyACM2' #Serial port for outputting processed data
        self.serIn='/dev/ttyACM1' #Serial port for MAVSDK connection

        #THE FOLLOWING DO NOT NEED TO BE EDITED

        self.detector=detector.CVProcessor(self.imW,self.imH)

        #Text parameters for the data label
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.fontScale = 0.5
        self.color = (0, 0, 0)
        self.thickness = 1

        self.ID=1 #Used to assign a unique identifier to each image saved
        self.folderName="radioImages0/" #Stores what folder data is saved to

        self.startTic=time.time()

        #Create a new folder for saved images
        if self.newFolder:
            self.createFolder()

        #Initialize serial output
        try:
            self.serOut=serial.Serial(self.serOut, 115200, timeout=10) #Connects to the Arduino over serial
            time.sleep(2)
            self.serOut.reset_input_buffer()
            self.serOut.write(b"start\n")
            read = self.serOut.readline().decode('utf-8').rstrip()
            print("CONNECTED TO SERIAL OUT")
        except:
            self.serOut=None
            print("ERROR: FAILED TO CONNECT TO DATA OUTPUT")

        #Initialize mavlink
        try:
            self.serIn = mavutil.mavlink_connection(self.serIn, baud=921600) # Adjust the port and baud rate if necessary
            self.serIn.wait_heartbeat()
            print("CONNECTED TO MAVLINK")
            self.serIn.mav.request_data_stream_send(self.serIn.target_system, self.serIn.target_component, mavutil.mavlink.MAV_DATA_STREAM_ALL, 5, 1) # Request all data streams at 5Hz
        except:
            self.serIn=None
            print("ERROR: FAILED TO CONNECT TO MAVLINK")
        pass


    def __createFolder(self): #Determines what folders exist and creates a new one for the flight, updates folderName
        i=0
        directoryFound=True
        while directoryFound==True:
            self.folderName="radioImages{}".format(i)
            path_input = os.path.join(sys.path[0], self.folderName)
            directoryFound = os.path.isdir(path_input)
            i+=1
        os.makedirs(path_input)
        self.folderName+="/"

        pass

    def dataUpdate(self, queueIn, queueOut): #Sends/receives data to/from the arduino
        loopTime=0
        while True:
            sendString=''
            if not queueIn.empty():
                sendString=str(queueIn.get())+'\n'
            #Send over serial
            if self.serOut!=None and len(sendString)>0:
                self.serOut.reset_input_buffer()
                self.serOut.write(bytes(sendString, 'utf-8'))
            if self.serIn!=None:
                msg = self.serIn.recv_msg()
                if msg!=None:
                    if msg.get_type()=='GLOBAL_POSITION_INT':
                        msg.lat=msg.lat/1e7
                        msg.lon=msg.lon/1e7
                        queueOut.put(msg)
        pass

    def processImage(self, dataOutQueue, dataInQueue, imageOutQueue): #Run an image through the CV program, add the relevant data, save the image
        ID=0
        loopFPS=0
        cap=cv2.VideoCapture(0)
        ret = cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = cap.set(3,self.imW)
        ret = cap.set(4,self.imH)

        #Create a data boarder
        labelinit = np.zeros((30,self.imW,3), np.uint8)
        labelinit[3:,:]=(255,255,255)
        while True:
            ret, image=cap.read()

            #Grab time for timestamp later
            imTic=time.time()-self.startTic

            #Run the dector program, and save the resulting image and data
            posIm,frame,cvData = self.detector.detect(image) #Run the image through the detector program

            if self.serIn!=None and not dataInQueue.empty():
                serData=dataInQueue.get()
            else:
                serData=None

            dataOutQueue.put(cvData)
            if self.saveData:
                imageOutQueue.put([posIm,imTic,cvData,serData])


    def storeImage(self, queue):
        ID=0
        if self.saveData:
            while True:
                
                processed=queue.get()
                #If saving data, write it to a csv
                if self.saveData:
                    #Record image data to a text file
                    txtfile=self.folderName+"imageData.txt"
                    with open(txtfile, 'a') as f:
                        f.write("{},{},{},{}".format(ID,processed[0],processed[1],processed[2]))
    
                ID+=1



#Initialize the framework
ANDRR=ANDRRFramework()
time.sleep(1)

#Setup display window
cv2.namedWindow('radioImage', cv2.WINDOW_NORMAL)

dataOutQueue=Queue()
dataInQueue=Queue()
imageOutQueue=Queue()

dataProcess=Process(target=ANDRR.dataUpdate, args=(dataOutQueue,dataInQueue, ))
saveImageProcess=Process(target=ANDRR.storeImage, args=(imageOutQueue, ))

dataProcess.start()
saveImageProcess.start()


ANDRR.processImage(dataOutQueue,dataInQueue,imageOutQueue)
