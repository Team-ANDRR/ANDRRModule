
# Import packages
import os
import cv2
import numpy as np
import sys
import time
import importlib.util
import csv
import serial
import detector
import imageSelection
from multiprocessing import Process,Queue
from pymavlink import mavutil


class ANDRRFramework:
    '''Framework for displaying CV detections over RCA'''
    def __init__(self):
        
        self.CVModel='edgetpu.tflite' #File name of cv model
        self.useTPU=True #Set to true if using ML accelerator
        self.newFolder=False #If true, a new folder will be created to save images and image data to
        self.DEBUG=True #If true, the display window isn't full screen to help with reading the terminal
        self.addImageLabel=True #If true, the program will add a label with ID and timestamp data to the bottom of all images
        self.showImage=True #If true, processed images will be saved to the pi
        self.saveData=True #If true, data from the detection program will be saved to a csv file
        self.saveImage=True #self.showImage #If true, images will be displayed on screen
        self.imW=800 #Display image resolution width
        self.imH=450 #Display image resolution height
        self.CamW=800 #Camera resolution width
        self.CamH=600 #Camera resolution height
        self.serOut='/dev/ttyACM1' #Serial port for outputting processed data
        self.serIn='/dev/ttyACM0' #Serial port for MAVSDK connection
        self.dataOut=True
        self.overwriteData=False
        self.viewMode="last" # * at the front indicates this is a override for the active mode
        self.GPSTimeOut=5 #How many seconds need to pass without GPS before readings should be ignored 
        self.cameraIndex=1 #Set to 0 for Pi camera, 1 for USB camera
        #THE FOLLOWING DO NOT NEED TO BE EDITED

        self.cap=cv2.VideoCapture(self.cameraIndex)
        ret = self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.cap.set(3,self.CamW)
        ret = self.cap.set(4,self.CamH)

        self.detector=detector.CVProcessor(self.CVModel,self.useTPU,self.imW,self.imH)

        self.ID=1
        self.cacheList=[0] #Array of positive detection sets
        self.GPSTic=time.time() #Time since last GPS update
        self.folderName="radioImages0/" #Stores what folder data is saved to if new folder is not made

        self.font=cv2.FONT_HERSHEY_SIMPLEX
        self.fontScale=0.5
        self.color=(0,0,0)
        self.thickness=1

        self.startTic=time.time()

        if self.viewMode=='recent' and self.saveImage:
            self.viewMode='recentSaved'

        if self.newFolder:
            self.createFolder()
        blank = np.zeros((self.imH+30,self.imW,3), np.uint8)
        blank[:-30,:]=(0,0,0)
        blank[-30:,:]=(255,255,255)
        imagePath=self.folderName + "blank.jpg"
        path_input = os.path.join(sys.path[0], imagePath)
        cv2.imwrite(path_input,blank)

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
                f.write("ID,Time,GPS,Detection,CVData\n")

        print('Setup Complete!')

        pass


    def createFolder(self): #Determines what folders exist and creates a new one for the flight, updates folderName
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

    def dataUpdate(self,dataOutQueue,GPSQueue,usrCmdQueue): #Sends/receives data to/from the arduino
        loopTime=0
        while True:
            
            dataOut=str(dataOutQueue.get())
            sendString=bytes(dataOut+'\n', 'utf-8')
            
            #Send over serial
            if self.serOut!=None and len(sendString)>0 and self.dataOut:
                self.serOut.reset_input_buffer()
                self.serOut.write(sendString)

            msg=None
            if self.serIn!=None:
                msg = self.serIn.recv_msg()
                if msg.get_type()=='GLOBAL_POSITION_INT':
                    msg.lat=msg.lat/1e7
                    msg.lon=msg.lon/1e7
                    GPSQueue.put(msg)
                elif msg.get_type()=='RC_CHANNELS':
                    usrCmdQueue.put(msg)

        pass

    def processImage(self, processOutQueue, dataOutQueue, GPSQueue): #Run an image through the CV program, add the relevant data, save the image

        ret, image=self.cap.read()
        image=cv2.resize(image,(self.imW,self.imH))

        #Grab time for timestamp later
        imTic=time.time()-self.startTic

        #Run the dector program, and save the resulting image and data
        frame,cvData = self.detector.detect(image) #Run the image through the detector program

        GPS=None
        if self.serIn!=None and not GPSQueue.empty():
            GPS=GPSQueue.get()

        cvData.insert(0,GPS)
        cvData.insert(0,imTic)
        cvData.insert(0,self.ID)
        dataOutQueue.put(cvData)
        processOutQueue.put([frame,cvData])
        self.ID+=1

        return frame

    def postProcess(self, processOutQueue, IDsQueue):
        #Create a data boarder
        labelinit = np.zeros((30,self.imW,3), np.uint8)
        labelinit[3:,:]=(255,255,255)
        GPStext="GPS: No connection"

        while True:
            frame,data=processOutQueue.get()
            ID,imTic,GPS,imPos,cvData=data

            if self.addImageLabel:

                # Create the ID string
                IDtext= "ID: " + str(ID)    

                # Create the timestamp string
                captureTime=round(imTic)
                seconds=captureTime%60
                minutes=int((captureTime-seconds)/60)
                timeStamp = "Time: " + str(minutes) + ":" + str(seconds).zfill(2)

                if GPS!=None:
                    self.GPSTic=time.time()
                    GPStext="GPS: " + str(GPS.lat) + "," + str(GPS.lon)
                else:
                    if (time.time()-self.GPSTic)>self.GPSTimeOut:
                        GPStext="GPS: No connection"

                #Create blank label
                label=labelinit.copy()

                # Add text to the boarder
                cv2.putText(label, timeStamp, (70,20), self.font, self.fontScale, self.color, self.thickness, cv2.LINE_AA)
                cv2.putText(label, IDtext, (self.imW-180,20), self.font, self.fontScale, self.color, self.thickness, cv2.LINE_AA)
                cv2.putText(label, GPStext, (int(self.imW*.25),20), self.font, self.fontScale, self.color, self.thickness, cv2.LINE_AA)

                #Add the boarder to the image
                frame=cv2.vconcat([frame,label])

            #If saving the image file, write it to the current folder
            if self.saveImage:
                # Name the image with a unique id
                imagePath=self.folderName + str(ID) + ".jpg"
                path_input = os.path.join(sys.path[0], imagePath)
                # Save the final image
                cv2.imwrite(path_input,frame)

            #If saving data, write it to a csv
            if self.saveData:
                #Record image data to a text file
                txtfile=self.folderName+"imageData.txt"
                with open(txtfile, 'a') as f:
                    f.write("{},{},{},{},{}\n".format(ID,imTic,GPS,imPos,cvData))

            self.cacheList[0]=ID

            if imPos: #If the image is positive
                if len(self.cacheList)>1:
                    #Checks if the current image is more than 5 frames away from a previous image
                    if 0 < (ID-self.cacheList[-1][-1]) < 5:
                        #If so, add all images between this dection and the last one (keeps sets together even if a few frames are lost)
                        for i in range(self.cacheList[-1][-1],ID):
                            self.cacheList[-1].append(i+1)
                    else:
                        #If this is a new dection, add it as a new row
                        self.cacheList.append([ID])
            
                else:
                    #This accounts for there being no previous image to compare against
                    self.cacheList.append([ID])

            IDsQueue.put(self.cacheList)


        pass

    def displayUpdate(self, usrCmdQueue,imageOutQueue,IDsQueue):
        imGet=imageSelection.imGet(self.folderName, self.viewMode)
        
        if self.showImage:
            while True:
                data=None
                if not usrCmdQueue.empty():
                    data=usrCmdQueue.get()
                IDs=IDsQueue.get()
                imageOutQueue.put(imGet.getImage(data,IDs))



#Initialize the framework
ANDRR=ANDRRFramework()


#Create display image
cv2.namedWindow('radioImage', cv2.WINDOW_NORMAL)
if not ANDRR.DEBUG:
    cv2.setWindowProperty('radioImage', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


#Create queues
processOutQueue=Queue(maxsize=1)
dataOutQueue=Queue(maxsize=1)
GPSQueue=Queue(maxsize=1)
usrCmdQueue=Queue(maxsize=1)
IDsQueue=Queue(maxsize=1)
imageOutQueue=Queue(maxsize=1)

#Create processes
imagePostProcess=Process(target=ANDRR.postProcess, args=(processOutQueue,IDsQueue, )) #Adds labels to images and saves them
dataProcess=Process(target=ANDRR.dataUpdate, args=(dataOutQueue,GPSQueue,usrCmdQueue, )) #Sends cv data and reads display commands
displayProcess=Process(target=ANDRR.displayUpdate, args=(usrCmdQueue,imageOutQueue,IDsQueue, )) #Determines what image to display based on display commands

#Start processes
dataProcess.start()
imagePostProcess.start()
displayProcess.start()


#Ending the program is done w/ ctrl+c on the pi or power off
while True:

    #Process an image
    recentImage=ANDRR.processImage(processOutQueue, dataOutQueue, GPSQueue)

    if ANDRR.showImage:
        #Update the image to be displayed
        if not imageOutQueue.empty():
            selectedImage=imageOutQueue.get()
            if selectedImage is None:
                selectedImage=recentImage
            else:
                selectedImage=cv2.imread(selectedImage)

            #show image
            cv2.imshow('radioImage',selectedImage)
            if cv2.waitKey(1) == ord('q'):
                break 

# Clean up
cv2.destroyAllWindows()


