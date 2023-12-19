"""
    Phidget Controls - use phidget components as dials, tuners, etc

    Requires:
    * Python 2.7.x
    * Python Interface http://www.xpluginsdk.org/python_interface.htm
    * Phidget library
    * typing library

    Installation:
    1. Download and install Python 2.7.x (64bit)
    2. Install Phidget library (python -m pip install Phidget22)
    3. Install typing library (python -m pip install typing)
    4. Download PythonInterface.zip from http://www.xpluginsdk.org/python_interface_latest_downloads.htm
    5. Unzip containing folder PythonInterface into XPLANEHOME/Resources/plugins
    6. Copy this script into XPLANEHOME/Resources/plugins/PythonScripts
    7. start X-Plane
    8. Select menu Plugins|Python Interface|Control Panel and confirm that the PhidgetControls plugin starts
    9. Open settings, Keyboard, bind fscode/phidgetcontrols/* actions to select interaction mode

    Customization:
    1. File PhidgetControlsConfig.py contains the configuration of phidgets and manipulators

"""
from XPLMProcessing import XPLMCreateFlightLoop, XPLMScheduleFlightLoop, XPLMDestroyFlightLoop
from XPLMDataAccess import XPLMFindDataRef, XPLMGetDatai, XPLMSetDatai, XPLMGetDataf, XPLMSetDataf
from XPLMUtilities import XPLMDebugString, XPLMFindCommand, XPLMCommandOnce, XPLMCreateCommand, \
    XPLMRegisterCommandHandler, XPLMUnregisterCommandHandler
from SandyBarbourUtilities import SandyBarbourPrint
from Phidget22.ErrorCode import ErrorCode
from Phidget22 import Phidget
from Phidget22.PhidgetException import PhidgetException
from typing import Type, Optional, Dict, Union
from operator import add, sub
import time

# Configuration: Global defaults
FLIGHT_LOOP_TIMER = 0.01
IGNORE_PHIDGET_ERROR = [ErrorCode.EPHIDGET_NOTATTACHED, ErrorCode.EPHIDGET_UNKNOWNVAL]  # type: [int]
Number = Union[float, int]


def log(message):
    # type: (object) -> None
    XPLMDebugString("" + str(message) + "\n")
    SandyBarbourPrint("" + str(message))


class PhidgetWrapper(object):
    type_id_2_phidget = {}  # type: Dict[ (type[Phidget], int), Phidget]

    def __init__(self, phidget_type, phidget_id):
        # type: (Type[Phidget], int) -> None
        self.last_open = 0

        key = (phidget_type, phidget_id)
        if key in PhidgetWrapper.type_id_2_phidget:
            self.wrapped = PhidgetWrapper.type_id_2_phidget[key]
        else:
            self.wrapped = phidget_type()
            self.wrapped.setDeviceSerialNumber(phidget_id)
            PhidgetWrapper.type_id_2_phidget[key] = self.wrapped
            PhidgetWrapper.log(self.wrapped, "Instantiated")
            self.open()

    @staticmethod
    def closeAll():
        # type: () -> None
        log("Closing " + str(len(PhidgetWrapper.type_id_2_phidget)) + " phidgets")
        for key, wrapped in PhidgetWrapper.type_id_2_phidget.iteritems():
            try:
                PhidgetWrapper.log(wrapped, "Closing")
                wrapped.close()
            except PhidgetException:
                pass
        PhidgetWrapper.type_id_2_phidget.clear()

    def open(self):
        # is the phidget attached?
        if self.wrapped.getAttached():
            return True

        # wait for at least 1s between open()
        if time.time() - self.last_open < 1:
            return False

        # try to open/attach
        self.last_open = time.time()
        try:
            PhidgetWrapper.log(self.wrapped, "Opening")
            self.wrapped.open()
        except PhidgetException, e:
            if e.code not in IGNORE_PHIDGET_ERROR:
                PhidgetWrapper.log(self.wrapped, e.description(), e.code)
            return False

        # can try
        return True

    @staticmethod
    def log(wrapped, message, code=None):
        # type: (Phidget, str, int) -> None
        if code:
            message = message + " (" + str(code) + ")"
        log("Phidget " + str(wrapped.__class__.__name__) + "#" + str(wrapped.getDeviceSerialNumber()) + ": " + message)

    # Proxy to phidget
    def __getattr__(self, attr):
        # ensure open
        self.open()
        # pass through
        return getattr(self.wrapped, attr)


class PositionProducer(object):
    # noinspection PyMethodMayBeStatic
    def getPosition(self):
        return None


class StateProducer(object):
    # noinspection PyMethodMayBeStatic
    def getState(self):
        # type: () -> object
        return None


class TrueStateProducer(object):
    # noinspection PyMethodMayBeStatic
    def getState(self):
        # type: () -> object
        return True


class NotStateProducer(object):
    def __init__(self, state_producer):
        # type: (StateProducer) -> None
        self.state_producer = state_producer

    # noinspection PyMethodMayBeStatic
    def getState(self):
        # type: () -> bool
        return not self.state_producer.getState()


class DeltaProducer(object):
    def __init__(self, position_producer):
        # type: (PositionProducer) -> None
        self.position_producer = position_producer
        self.position = None

    def getDelta(self):
        # type: () -> int
        new_position = self.position_producer.getPosition()
        if new_position is None:
            return 0
        # first result ever?
        if self.position is None:
            self.position = new_position
            return 0
        # calc delta
        old_position = self.position
        self.position = new_position
        delta = old_position - self.position
        return delta


class NotchedPositionProducer(PositionProducer):
    def __init__(self, position_producer, notch_size):
        # type: (PositionProducer, int) -> None
        self.position_producer = position_producer
        self.notch_size = notch_size
        self.position = None

    # get position
    def getPosition(self):
        # type: () -> Optional[int]
        new_position = self.position_producer.getPosition()
        if not new_position:
            return None

        # no change?
        if new_position == self.position:
            return int(self.position / self.notch_size)

        # check if inside notch
        inside_position = new_position % self.notch_size
        if self.position is None or inside_position < self.notch_size / 2:
            # if yes, follow producer
            self.position = new_position
        else:
            # if no, follow to the closest notch
            op = add if new_position < self.position else sub
            self.position = op(new_position, self.notch_size/2)

        # done
        return int(self.position / self.notch_size)


class ClickProducer(object):
    def __init__(self, digital_input_producer):
        # type: (StateProducer) -> None
        self.digital_input_producer = digital_input_producer
        self.state = None  # type: Union[bool, None]

    # get delta change
    def isClicked(self):

        new_state = self.digital_input_producer.getState()

        # calculate click
        if self.state is None:
            old_state = new_state
        else:
            old_state = self.state
        self.state = new_state

        # done
        return not old_state and self.state


class Interaction(object):
    @staticmethod
    def _getPhidget(phidget):
        # type: ( str ) -> Phidget
        from PhidgetControlsConfig import PHIDGETS

        phidget_type, phidget_id = PHIDGETS[phidget]  # type: (type[Phidget], int)
        return PhidgetWrapper(phidget_type, phidget_id)

    def tick(self):
        pass


class Rotate(Interaction):
    def __init__(self, position_producer, notch_size, xref, min_value, max_value, step):
        # type: (str, int, str, Number, Number, Number) -> None
        self.delta_producer = DeltaProducer(NotchedPositionProducer(self._getPhidget(position_producer), notch_size))
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.ref = XPLMFindDataRef(xref)
        if isinstance(min_value, float):
            self.getter = XPLMGetDataf
            self.setter = XPLMSetDataf
        else:
            self.getter = XPLMGetDatai
            self.setter = XPLMSetDatai

    def tick(self):
        # type: () -> None
        delta = self.delta_producer.getDelta()
        if not delta:
            return
        val = self.getter(self.ref) + (delta * self.step)
        val = self.min_value + ((val - self.min_value) % (self.max_value - self.min_value))
        self.setter(self.ref, val)


class SetDigit(Interaction):
    def __init__(self, position_producer, if_state_producer, xref, digit):
        # type: (str, Optional[str], str, int) -> None
        self.delta_producer = DeltaProducer(NotchedPositionProducer(self._getPhidget(position_producer), 10))
        if if_state_producer:
            if if_state_producer.startswith("!"):
                self.if_state_producer = self._getPhidget(if_state_producer[1:])
            else:
                self.if_state_producer = NotStateProducer(self._getPhidget(if_state_producer))
        else:
            self.if_state_producer = TrueStateProducer()
        self.digit = digit
        self.ref = XPLMFindDataRef(xref)
        self.getter = XPLMGetDatai
        self.setter = XPLMSetDatai

    def tick(self):
        delta = self.delta_producer.getDelta()
        if not delta:
            return
        if self.if_state_producer.getState():
            return
        val = self.getter(self.ref)
        increment_digit = 10 ** (self.digit-1)
        modulo = increment_digit * 10
        remainder = (val + delta*increment_digit) % modulo
        quotient = int(val / modulo) * modulo
        val = quotient + remainder
        self.setter(self.ref, val)


class SetValue(Interaction):
    delta_producer = None  # type: DeltaProducer

    def __init__(self, position_producer, acceleration_state_producer, xref, increment, accelerated_increment,
                 min_value, max_value):
        # type: (Phidget, str, Optional[str], str, Number, Optional[Number], Number, Number) -> None
        self.delta_producer = DeltaProducer(NotchedPositionProducer(self._getPhidget(position_producer), 10))
        self.state_producer = self._getPhidget(acceleration_state_producer) if acceleration_state_producer \
            else StateProducer()  # type: StateProducer
        self.increment = increment
        self.accelerated_increment = accelerated_increment
        self.min = min_value
        self.max = max_value
        self.ref = XPLMFindDataRef(xref)
        self.use_float = isinstance(increment, float)
        if self.use_float:
            self.getter = XPLMGetDataf
            self.setter = XPLMSetDataf
        else:
            self.getter = XPLMGetDatai
            self.setter = XPLMSetDatai

    def tick(self):
        delta = self.delta_producer.getDelta()
        if not delta:
            return
        inc = self.accelerated_increment if self.state_producer.getState() else self.increment
        val = min(self.max, max(self.min, self.getter(self.ref) + delta * inc))
        self.setter(self.ref, val)


class Tune(Rotate):
    def __init__(self, position_producer, xref, min_value, max_value, inc):
        # type: (str, str, Number, Number, Number) -> None
        Rotate.__init__(self, position_producer, 10, xref, min_value, max_value, inc)


class SetHeading(Rotate):
    def __init__(self, position_producer, xref):
        # type: (str, str) -> None
        Rotate.__init__(self, position_producer, 2, xref, 0.0, 360.0, 1.0)


class SetBearing(Rotate):
    def __init__(self, position_producer, xref):
        # type: (str, str) -> None
        Rotate.__init__(self, position_producer, 2, xref, 0.0, 360.0, 1.0)


class Click(Interaction):
    def __init__(self, state_producer, xref):
        # type: (str, str) -> None
        self.click_producer = ClickProducer(self._getPhidget(state_producer))
        self.ref = XPLMFindCommand(xref)

    def tick(self):
        if self.click_producer.isClicked():
            XPLMCommandOnce(self.ref)


class Command(object):
    flight_loop = None  # type: FlightLoop

    def __init__(self, mode, flight_loop, plugin):
        # type: (str, FlightLoop, PythonInterface) -> None
        self.mode = mode
        self.flight_loop = flight_loop
        self.plugin = plugin
        self.cmd = XPLMCreateCommand("fscode/phidgetcontrols/" + mode, "Set current mode to " + mode)
        self.callback = self.handle_callback
        log("Registering command for mode " + self.mode)
        XPLMRegisterCommandHandler(self.plugin, self.cmd, self.callback, 0, 0)

    def stop(self):
        log("Unregistering command for mode " + self.mode)
        XPLMUnregisterCommandHandler(self.plugin, self.cmd, self.callback, 0, 0)

    def handle_callback(self, _in_command, in_phase, _in_refcon):
        if in_phase == 0:
            log('Setting current interactions for ' + self.mode)
            self.flight_loop.setCurrentMode(self.mode)


class FlightLoop:

    def __init__(self, plugin):

        self.plugin = plugin

        # set up commands for modes of interactions
        self.interactions = []

        from PhidgetControlsConfig import INTERACTIONS
        self.commands = map(lambda mode: Command(mode, self, plugin), INTERACTIONS.keys())

        # hook-up into X loop
        log("Registering flight loop")
        self.loop_callback = self.handle_loop
        _CreateFlightLoop_t = [1, self.loop_callback, 0]
        self.loop = XPLMCreateFlightLoop(plugin, _CreateFlightLoop_t)
        self.loop_timer = FLIGHT_LOOP_TIMER
        XPLMScheduleFlightLoop(plugin, self.loop, self.loop_timer, 1)

    def handle_loop(self, _elapsed_me, _elapsed_sim, _counter, _refcon):
        try:
            for interaction in self.interactions:
                interaction.tick()
        except PhidgetException, e:
            if e.code not in IGNORE_PHIDGET_ERROR:
                log(e.description + " (" + str(e.code) + ")")

        return FLIGHT_LOOP_TIMER

    def stop(self):
        log("Unregistering flight loop")
        XPLMDestroyFlightLoop(self.plugin, self.loop)
        PhidgetWrapper.closeAll()
        for command in self.commands:
            command.stop()

    def setCurrentMode(self, mode):
        # type: (str) -> None
        from PhidgetControlsConfig import INTERACTIONS
        self.interactions = INTERACTIONS[mode]()


# Plugin boilerplate
class PythonInterface:

    def __init__(self):
        self.flight_loop = None
        self.Desc = None
        self.Sig = None
        self.Name = None

    def XPluginStart(self):
        # boilerplate
        self.Name = "PhidgetControls"
        self.Sig = "fscode.phidgets"
        self.Desc = (
            "Plug-in for controlling cockpit functions via Phidgets, for example "
            " radio frequencies on a Phidget Encoder knob.")

        log(self.Name + ": Plugin start")

        # set up flight loop
        self.flight_loop = FlightLoop(self)

        # complete
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        log(self.Name + ": Plugin stop")

        self.flight_loop.stop()

    # noinspection PyMethodMayBeStatic
    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, _in_from, _in_message, _in_param):
        pass

# import wave
# import os
# current_dir = os.getcwd()
# file_wave_click = os.path.join(current_dir, "Resources/sounds/systems/click.wav")
# log("Loading "+file_wave_click)
# self.wave_click = wave.open(str(file_wave_click), 'rb')
