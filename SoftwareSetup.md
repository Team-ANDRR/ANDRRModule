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

The majority of changes you'll need to make initially will be to the ANDRR Framework file. These include specifying where files are stored, what parts are turned on or off, where data is outputed, and what serial connections coreespond to what physical systems. Read through the first section of the init function for the ANDRRFramework class, and update the variables according to the comments
