<img src="https://github.com/nmeier/PhidgetControls/assets/312857/7b361738-f153-4490-a73d-676cd98de060" width="256">
<img src="https://github.com/nmeier/PhidgetControls/assets/312857/6a333ded-ff21-43a1-9cf8-bd96ea125798" width="256">

Phidget Controls - use phidget components as dials, tuners, buttons in [X-Plane](https://www.x-plane.com/)

Requires:
* X-Plane 11
* Python 2.7.x
* Python Interface http://www.xpluginsdk.org/python_interface.htm
* Phidget library
* typing library

Installation:
1. Download and install Python 2.7.x (64bit)
2. Install Phidget and typing library (cd c:/python27 ; python -m pip install Phidget22; python -m pip install typing)
3. Download PythonInterface.zip from http://www.xpluginsdk.org/python_interface_latest_downloads.htm and unzip containing folder "PythonInterface" into XPLANEHOME/Resources/plugins
4. Download scripts [here](https://codeload.github.com/nmeier/PhidgetControls/zip/refs/heads/master) unzip contained *.py files into XPLANEHOME/Resources/plugins/PythonScripts (no sub-directories)
5. Start X-Plane and select menu Plugins|Python Interface|Control Panel and confirm that the PhidgetControls plugin starts
7. Customize PhidgetControlsConfig.py which contains the configuration for interactions and available phidgets
8. Open X-Plane settings for Keyboard and bind fscode/phidgetcontrols/* actions to keys for selection of active interaction mode
9. Select current active interaction via bindings configured in previous step and manipulate phidgets for interactions' declared dials and buttons

