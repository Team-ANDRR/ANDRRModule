The exact nature of the assembly of an ANDRR module will depend on the system it is connected to. The exact connection locations, what parts are used, and how they are mounted will vary based on what parts the platform UAS has, the UAS structure, and the compnents used in the module itself. As a result, this guide lists out the general connections required; what exactly said connections will look like is left to the user.

1. Rasberry Pi - UAS battery 
  This connection uses the 5v 2A power supply to regulate the voltage from the UAS battery down to a usable level by the Pi. This regulator should be capable of supplying at least 2A to power the Pi adn connnected accessories. If a more computationally intensive program is used, or additional sensors/boards are connected to the Pi, a higher current rating may be required.

2. Rasberry Pi - Coral USB accelerator
  The coral accelerator recieves power and data via a USB cable connected to the Pi. Make sure this cable connects to a USB3.0 port (colored blue) on the raspberry pi for fastest data transfer

3. Raspberry Pi - FPV transmitter
  The Pi transmits video data to the FPV transmitter via a analog output pin. For a Pi 4 this connection is made using the barrel jack. For a Pi 5 it is made using a dedicated TV pin. In addition to the signal out, the Pis and transmitters grounds should be tied together

4. FPV transmitter - USB battery
  The FPV transmitter will need to be powered off the UAS battery. This may or may not requried a voltage regulator, depending on the cell count of the battery and the voltage requirement of the transmitter

5. Raspberry Pi - UAS flight computer
   The Pi connects to the platform flight computer via a serial connection using a Pi USB port.

6. Raspberru Pi - Companion computer
   The exact nature of this connection will depend on what computer is used. To provide both a power and data connection, use a USB cable. For more power intesive companion computers, a dedicated power supply may be requuired.

7. Raspberry Pi - Camera
   What this connection looks like will vary based on the camera used. If a Pi camera is used, connect via the ribbon cable port. If a USB compatible camera is used, connect via USB.

As a large number of these connections use the Pi's USB ports, its important to note down what connections correspond to what devices. Starting with no USB devices plugged into the Pi, use the command line to list connected devices via
```
ls /dev/tty*
```
Then, make each connection, rerun the command, and note what new devices pop up. These tags will then be used to update the software.
