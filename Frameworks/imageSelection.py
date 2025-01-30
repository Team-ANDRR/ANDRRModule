# Import packages
import os
import cv2
import numpy as np
import sys
import time
import importlib.util



class imGet:
    def __init__(self, foldername,viewMode):
        self.foldername=foldername
        self.dispID=[0,0,1,0,0,0] #Holds the image being shown. The first 2 entries are a position in positive IDs, the third determines if cached detections are being shown, the forth determines if the screen is blank or not, the fifth determines if the last image should be held or not, the sixth is used when showing all images, and simply holds the ID
        
        #Determines if the program needs to wait before enacting a stick command when moving through cached images to make control easier
        self.updateTime=.5
        self.updateTic=time.time() 
        
        #Used with dispID[3] to determine how long the screen should be blank for
        self.setBlankTime=.5
        self.setBlankTic=time.time()

        #Used to determine when the program should move to the next image in a set
        self.setUpdateTime=1
        self.setUpdateTic=time.time()

        #Used to determine when the program should return to the passive mode following no inputs
        self.timeOutTime=6        
        self.timeOutTic=time.time() 

        self.setScrubbing=1 #Ramp rate for how many sets the system scrubs through each second with manual control
        self.imageScrubbing=0.1 #Ramp rate for how many images the system scrubs through each second with manual control

        #Used to determine how long a input has been held
        self.holdScrubTic=time.time()
        self.prevScrub=0

        self.loopNum=3 #For use with set mode, determines how many times a set loops before moving on the the next
        self.loopCount=0 #Used with loopNum

        #Define user commands
        self.scrubControl=0
        self.holdControl=0

        self.passiveMode=viewMode
        self.modeOverride=True
        if self.passiveMode[0]=='*': #Determine if mode override is used
            self.passiveMode=self.passiveMode[1:] 
            self.modeOverride=False


        pass


    def getImage(self, data, IDs):
        self.cacheList=IDs
        self.ID=self.cacheList.pop(0)
        self.telemetryData=data

        if self.telemetryData!=None:
            self.updateControl()

        #Check if there are no images to sort through
        if self.passiveMode=="live" and self.modeOverride:
            return None
        elif len(self.cacheList)<1:
            self.dispID[5]=self.ID
        elif self.telemetryData==None or self.modeOverride:
            self.getID_passive() #Otherwise compute the new ID
        else:
            self.getID_active()

       
        imFilePath=None
        if self.dispID[3]: #If setting blank
            imFilePath="blank.jpg"
        elif self.dispID[2]==0: #If showing live
            return None
        elif self.dispID[5]!=0: #If specific ID is used
            imFilePath="{}.jpg".format(self.dispID[5])
        else: #If showing cached images:
            imFilePath="{}.jpg".format(self.cacheList[self.dispID[0]][self.dispID[1]])  


        if imFilePath!=None:
            return self.foldername+imFilePath
        else:
            return None

        pass


    def updateControl(self):

        if self.telemetryData.chan4_raw==0:
            self.telemetryData=None
            return

        if self.telemetryData.chan4_raw>700:
            self.scrubControl=1
        elif self.telemetryData.chan4_raw<300:
            self.scrubControl=-1
        else:
            self.scrubControl=0

        if self.prevScrub!=self.scrubControl: #If change in scrub value
            self.holdScrubTic=time.time()
        self.prevScrub=self.scrubControl

        if self.telemetryData.chan6_raw>700:
            self.holdControl=1
        elif self.telemetryData.chan6_raw<300:
            self.holdControl=-1
        else:
            self.holdControl=0

        if self.telemetryData.chan8_raw>700:
            self.controlMode=1
        elif self.telemetryData.chan8_raw<300:
            self.controlMode=-1
        else:
            self.controlMode=0

        if self.scrubControl!=0 or seld.holdControl!=0: #Reset timeout clock if theres a input
            self.timeOutTic=time.time()

        if (time.time()-self.timeOutTic)>self.timeOutTime: #If the timout clock runs out, set telemetry data to none to kick the system into passive mode
            self.telemetryData=None

        pass


    def getID_passive(self):

        if self.passiveMode=="last":
            #For showing the last image with label
            self.dispID[5]=self.ID
            pass

        if self.passiveMode=="recentDetected":
            #For showing the most recent positive image
            self.dispID[2]=1 #Set to display cached images
            self.dispID[4]=0 #Remove any hold
            self.dispID[5]=self.cacheList[-1][-1] #Show the most recent image with a detection
            pass

        if self.passiveMode=="sets":
            #For displaying sets without control
            self.dispID[2]=1 #Set to display cahced images
            self.dispID[4]=0 #Remove any hold
            self.dispID[5]=0 #Remove any ID used in the "all images" mode 

            if self.dispID[3]:
                if(time.time()-self.setBlankTic)>self.setBlankTime: #If reseting from blank
                    self.dispID[3]=0 #Remove the set blank indicator and return the ID
                pass

            if (time.time()-self.setUpdateTic)>self.setUpdateTime: #If time to move to the next image in the set
                self.dispID[1]+=1
                self.setupdateTic=time.time()

                #If you have exceeded the number of images in a set, loop back to the first image
                if self.dispID[1]>len(self.cacheList[self.dispID[0]])-1:
                    self.dispID[1]=0
                    self.loopCount+=1

                    #If the set has looped for the proper number, move to the next set
                    if self.loopCount>=self.loopNum:
                        self.loopCount=0
                        self.dispID[0]+=1

                        #Call for blank and set time
                        self.dispID[3]=1
                        self.setBlankTic = time.time()


                    #If you have exceeded the number of sets loop back to the first set
                    if self.dispID[0]>len(self.cacheList)-1:
                        self.dispID[0]=0

        pass


    def getID_active(self):

        if self.controlMode==0: #If telemetry is set to all images
            if self.dispID[3]:
                if(time.time()-self.setBlankTic)>self.setBlankTime: #If reseting from blank
                    self.dispID[3]=0 #Remove the set blank indicator and return the ID
                pass

            self.dispID[0:5]=[0,0,1,0,0] #Set to show cached images, clear everything but the ID to show

            if (time.time()-self.updateTic)>self.updateTime: #Check if the stick being left or right should be read againt
                self.updateTic=time.time()

                if self.scrubControl==-1: #If moving backwards
                    if self.dispID[5]==0: #If previous ID is not defined
                        self.dispID[5]=self.ID-1
                    else:
                        self.dispID[5]-=int(self.setScrubbing*(time.time()-self.holdScrubTic)+1)
                        if self.dispID[5]<1: #If you reach the beginning of the list, loop back around
                            self.dispID[5]=self.ID
                            #Call for blank and set time
                            self.dispID[3]=1
                            self.setBlankTic = time.time()

                elif self.scrubControl==1: #If moving forwards
                    if self.dispID[5]==0:  #If previous ID is not defined
                        self.dispID[5]=1
                    else:
                        self.dispID[5]+=int(self.setScrubbing*(time.time()-self.holdScrubTic)+1)
                        if self.dispID[5]>self.ID: #If you reach the most up to date image, loop back to the start
                            self.dispID[5]=1
                            #Call for blank and set time
                            self.dispID[3]=1
                            self.setBlankTic = time.time()

                elif self.holdControl==1: #If stick is only up
                    self.dispID=[0,0,0,1,0,0] #reset to live detections
                    self.setBlankTic = time.time() #Call for blank and set time
                
            pass

        else: #Telemetry set to use image sets
            self.dispID[4]=0 #Remove the hold

            self.dispID[5]=0 #Remove the ID used in the all images mode 

            if self.dispID[3]:
                if(time.time()-self.setBlankTic)>self.setBlankTime: #If reseting from blank
                    self.dispID[3]=0 #Remove the set blank indicator and return the ID
                pass

            if (time.time()-self.updateTic)>self.updateTime and len(self.cacheList)>0: #Check if the stick being left or right should be read againt
                if self.scrubControl==-1: #If stick is left
                    if self.dispID[2]: #If already in the cache
                        if self.holdControl==-1: #If stick is down
                            self.dispID[1]-=int(self.imageScrubbing*(time.time()-self.holdScrubTic)+1)
                            if self.dispID[1]<0:
                                self.dispID[1]=len(self.cacheList[self.dispID[0]])-1
                        else: #If stick is not down
                            self.dispID[0]-=int(self.setScrubbing*(time.time()-self.holdScrubTic)+1)
                            self.dispID[1]=0
                            if self.dispID[0]<0:
                                self.dispID[0]=len(self.cacheList)-1
                            self.dispID[3], self.setBlankTic = 1, time.time() #Call for blank and set time
                    else: #If not already in the cache
                        self.dispID=[len(self.cacheList)-1,0,1,1,0,0] #Display the last detection
                        self.setBlankTic = time.time() #Call for blank and set time

                    self.updateTic=time.time() #Update the update tic
                    self.setUpdateTic=time.time()
                    pass

                elif self.scrubControl==1:#If stick is right
                    if self.dispID[2]: #If already in the cache
                        if self.telemetryData['p']==-1: #If stick is down
                            self.dispID[1]+=int(self.imageScrubbing*(time.time()-self.holdScrubTic)+1)
                            if self.dispID[1]>len(self.cacheList[self.dispID[0]])-1:
                                self.dispID[1]=0
                        else: #If stick is not down
                            self.dispID[0]+=int(self.setScrubbing*(time.time()-self.holdScrubTic)+1)
                            self.dispID[1]=0
                            if self.dispID[0]>len(self.cacheList)-1:
                                self.dispID[0]=0
                            self.dispID[3], self.setBlankTic = 1, time.time() #Call for blank and set time
                    else: #If not already in the cache
                        self.dispID=[0,0,1,1,0,0] #Display the first detection
                        self.setBlankTic = time.time() #Call for blank and set time

                    self.updateTic=time.time() #Update the update tic
                    self.setUpdateTic=time.time()
                    pass

            if self.holdControl==-1 and self.scrubControl==0: #If stick is only down
                self.setUpdateTic=time.time()
                self.dispID[4]=1
                pass #Keep the current id

            elif self.holdControl==1: #If stick is only up
                self.dispID=[0,0,0,1,0,0] #reset to live detections
                self.setBlankTic = time.time() #Call for blank and set time
                pass

            elif self.dispID[2]: # If already in the cache and no stick input
                if (time.time()-self.setUpdateTic)>self.setUpdateTime: #If time to move to the next image in the set
                    self.dispID[1]+=1
                    if self.dispID[1]>len(self.cacheList[self.dispID[0]])-1:
                        self.dispID[1]=0
                pass

            else: #Catch other states
                self.dispID=[0,0,0,0,0,0] #Show live detection, no blank
                pass


        pass