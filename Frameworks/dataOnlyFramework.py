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
        
        self.CVModel='edgetpu.tflite' #File name of cv model
        self.useTPU=True #Set to true if using ML accelerator
        self.newFolder=False #If true, a new folder will be created to save images and image data to
        self.DEBUG=True #If true, the display window isn't full screen to help with reading the terminal
        self.saveData=True #If true, data from the detection program will be saved to a csv file
        self.imW=800 #Display image resolution width
        self.imH=450 #Display image resolution height
        self.CamW=800 #Camera resolution width
        self.CamH=600 #Camera resolution height
        self.serOut='/dev/ttyACM1' #Serial port for outputting processed data
        self.serIn='/dev/ttyACM0' #Serial port for MAVSDK connection
        self.overwriteData=True
        self.cameraIndex=1

        #THE FOLLOWING DO NOT NEED TO BE EDITED

        self.cap=cv2.VideoCapture(self.cameraIndex, cv2.CAP_V4L2)
        ret = self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.cap.set(3,self.CamW)
        ret = self.cap.set(4,self.CamH)

        self.detector=detector.CVProcessor(self.CVModel,self.useTPU,self.imW,self.imH)

        #Text parameters for the data label
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.fontScale = 0.5
        self.color = (0, 0, 0)
        self.thickness = 1

        self.ID=1 #Used to assign a unique identifier to each image saved
        self.folderName="radioImages0/" #Stores what folder data is saved to if new folder is not made

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


        if self.saveData:
            if self.overwriteData:
                writeMethod='w'
            else:
                writeMethod='a'
            txtfile=self.folderName+"imageData.txt"
            with open(txtfile, writeMethod) as f:
                f.write("Time,SerialData,CVData\n")

        print('Setup Complete!')

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
        ID=self.ID

        #Create a data boarder
        labelinit = np.zeros((30,self.imW,3), np.uint8)
        labelinit[3:,:]=(255,255,255)
        while True:
            ret, image=self.cap.read()
            image=cv2.resize(image,(self.imW,self.imH))

            #Grab time for timestamp later
            imTic=time.time()-self.startTic

            #Run the dector program, and save the resulting image and data
            frame,cvData = self.detector.detect(image) #Run the image through the detector program

            if self.serIn!=None and not dataInQueue.empty():
                serData=dataInQueue.get()
            else:
                serData=None


            dataOutQueue.put(cvData)
            if self.saveData:
                imageOutQueue.put([imTic,serData,cvData])



    def storeData(self, queue):
        if self.saveData:
            while True:
                imTic,serData,cvData=queue.get()
                #If saving data, write it to a csv
                if self.saveData:
                    #Record image data to a text file
                    txtfile=self.folderName+"imageData.txt"
                    with open(txtfile, 'a') as f:
                        f.write("{},{},{}\n".format(imTic,serData,cvData))
    



#Initialize the framework
ANDRR=ANDRRFramework()
time.sleep(1)

#Setup display window
cv2.namedWindow('radioImage', cv2.WINDOW_NORMAL)

dataOutQueue=Queue()
dataInQueue=Queue()
imageOutQueue=Queue()

dataProcess=Process(target=ANDRR.dataUpdate, args=(dataOutQueue,dataInQueue, ))
saveDataProcess=Process(target=ANDRR.storeData, args=(imageOutQueue, ))

dataProcess.start()
saveDataProcess.start()


ANDRR.processImage(dataOutQueue,dataInQueue,imageOutQueue)
