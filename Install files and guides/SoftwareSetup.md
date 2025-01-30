The ANDRR Module comes with a series of frameworks to help you get started. These vary based on intended mission, and include:
1. Optimized live CV overlay
2. Optimized live CV processing data output
3. CV data output and image transmission for semi autonomous systems
4. Live CV detections and reporting for surveying work


Regardless of the framework used, the ANDRR module uses the following programs:
1. An ANDRR Framework - responsible for running the supporting structure around the CV processor
2. A detector file - responsible for running the CV model and reporting the required data
3. A tflite file - the CV model
4. A labelmap file - stores class labels for the CV model
5. If using the surveying framework, a imageSelection file is used to handle transmitting processed images to the ground


The majority of changes you'll need to make initially will be to the ANDRR Framework file. These include (but are not limited to) the following:
1. Set DEBUG to false for full screen image display
2. Update the serial and mavlink usb ports to the correct values (run ```ls /dev/tty*``` in the terminal to see connected devices)
3. Update the cameraIndex to match your desired camera (start with 0)
4. Update imW and imH to fit the size of your display screen
5. Update CamW and CamH to fit the camera your using. Keeping these values as close to imW and imH as possible will reduce processing time
6. If using a pi camera you can set CamW and CamH to imW and imH, then comment out the ```image=cv2.resize(image,(self.imW,self.imH))``` line in the processor function for faster FPS.
To see all adjustable parameters, read through the first section of the init function for the ANDRRFramework class.


The detector file can be modified to return different data, use a different model, or return a different format of processed images. The only requirements are as follows:
1. The init function takes in the cv model name, whether it used the AI accelerator or not, and the image width and height
2. The detect function returns the image, and any associated data you wish to add.
The cv model and labelmap files will also need to be updated, after which the system will use the new model.
