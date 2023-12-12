<img src="https://github.com/nmeier/PhidgetControls/assets/312857/7b361738-f153-4490-a73d-676cd98de060" width="256">
<img src="https://github.com/nmeier/PhidgetControls/assets/312857/6a333ded-ff21-43a1-9cf8-bd96ea125798" width="256">

Phidget Controls - use phidget components as dials, tuners, etc

Requires:
* X-Plane 11
* Python 2.7.x
* Python Interface http://www.xpluginsdk.org/python_interface.htm
* Phidget library
* typing library

Installation:
1. Download and install Python 2.7.x (64bit)
2. Install Phidget library (python -m pip install Phidget22
3. Install typing library (python -m pip install typing)
4. Download PythonInterface.zip from http://www.xpluginsdk.org/python_interface_latest_downloads.htm
5. Unzip containing folder PythonInterface into XPLANEHOME/Resources/plugins
6. Copy this script into XPLANEHOME/Resources/plugins/PythonScripts
7. start X-Plane
8. Select menu Plugins|Python Interface|Control Panel and confirm that the PhidgetControls plugin starts
9. Open settings, Keyboard, bind fscode/phidgetcontrols/* actions to select interaction mode
10. Manipulate those dials and buttons

Customization:
* File PhidgetControlsConfig.py contains the configuration of phidgets and interactions
