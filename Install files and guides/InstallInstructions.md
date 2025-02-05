The following code is intended for use on 64 bit LITE Bullseye or Bookworm Rasbian images. Version dependant commands will be noted as such

1. Update system:
```
sudo apt-get update
sudo apt-get dist-upgrade
```

2. Install lite desktop:
```
sudo apt install xserver-xorg raspberrypi-ui-mods
sudo raspi-config
```
Set boot option to automatically sign in to desktop

3. Install pip3:
```
sudo apt-get install python3-pip
```

4. If using Bookworm, change python version to 3.9

4.a Install dependinces (this may take a while)
```
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
```
4.b Download and compile python 3.9
```
wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tar.xz
tar xf Python-3.9.0.tar.xz
cd Python-3.9.0
./configure --enable-optimizations --prefix=/usr
make
```
4.c Once the compilation completes install the build
```
sudo make altinstall
```
4.d Cleanup
```
cd ..
sudo rm -r Python-3.9.0
rm Python-3.9.0.tar.xz
. ~/.bashrc
```
4.e Add python3.9 to the python alternatives list
```
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1
```
4.f Make python3.9 default
```
sudo update-alternatives --config python
```
Enter the selection number for python3.9

5. Setup folder for file management:

5.a Create ANDRRModule folder
```
mkdir ANDRRModule
cd ANDRRModule
```
5.b Create processedImages0 folder
```
mkdir radioImages0
```

6. Create virtual env
```
sudo apt-get install python3-venv
python3 -m venv ANDRRModuleEnv
source ANDRRModuleEnv/bin/activate
```

7. Install everything else:

Download the pi_requirements folder and move it to the ANDRRModule folder, then run the following
```
bash pi_requirments.sh
```

8. Create launcher.sh script
```
nano launcher.sh
```
8.a Write script
```
#!/bin/bash
#launcher.sh

cd /home/andrr/tflite1/dataFramework
source ANDRRModuleEnv/bin/activate
python <program to run>
```
8.b Add launcher to chmod
```
sudo chmod 755 launcher.sh
```
8.c Add launcher to desktop start
```
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart 
```
At the bottom of the file, add ```lxterminal -e bash <path to sh script>```


9. Setup analog output:

In config.txt look for:
```
# uncomment for composite PAL
#sdtv_mode=2
```
Replace this with the following:
```
sdtv_mode=0
sdtv_aspect=1
enable_tvout=1
```

10. Adjust desktop size to fit monitor

In the same config.txt file as step 9, adjust the overscan values. For a small FPV monitor, try starting with 16 for each side
