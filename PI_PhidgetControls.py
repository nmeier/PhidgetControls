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
import logging
from time import time
from logging import Handler
from traceback import format_exception, format_exc

from XPLMProcessing import XPLMCreateFlightLoop, XPLMScheduleFlightLoop, XPLMDestroyFlightLoop
from XPLMDataAccess import XPLMFindDataRef, XPLMGetDatai, XPLMSetDatai, XPLMGetDataf, XPLMSetDataf
from XPLMUtilities import XPLMDebugString, XPLMFindCommand, XPLMCommandOnce, XPLMCreateCommand, \
    XPLMRegisterCommandHandler, XPLMUnregisterCommandHandler
from SandyBarbourUtilities import SandyBarbourPrint
from Phidget22 import Phidget
from Phidget22.PhidgetException import PhidgetException
from typing import Optional, Union, List
from operator import add, sub
from PhidgetControlsCache import get_phidget, close_all_phidgets, log_phidget_exception, ensure_phidgets_opened

# Configuration: Global defaults
FLIGHT_LOOP_TIMER = 0.01
FLIGHT_LOOP_SEQUENCE = 0

Number = Union[float, int]


class XPlaneLogger(Handler):

    def __init__(self):
        Handler.__init__(self)

    def emit(self, record):
        msg = record.getMessage()
        XPLMDebugString("%s: %s\n" % ('PhidgetControls', msg))
        SandyBarbourPrint("%s: %s" % ('PhidgetControls', msg))


class PositionProducer(object):
    # noinspection PyMethodMayBeStatic
    def getPosition(self):
        return None


class StateProducer(object):
    # noinspection PyMethodMayBeStatic
    def getState(self):
        # type: () -> object
        return None


class RelativePositionProducer(PositionProducer):

    def __init__(self, position_producer):
        self.position_producer = position_producer
        self.starting_position = None
        self.last_position = None
        self.last_loop_sequence = None

    def getPosition(self):

        # get new position, have none? don't have a position
        new_position = self.position_producer.getPosition()
        if not new_position:
            return None

        # first position? starting offset
        if not self.starting_position:
            self.starting_position = new_position
            self.last_position = new_position
            self.last_loop_sequence = FLIGHT_LOOP_SEQUENCE
            return 0

        # are we not in sequence anymore and need to start fresh?
        if self.last_loop_sequence != FLIGHT_LOOP_SEQUENCE-1:
            self.starting_position = new_position-(self.last_position-self.starting_position)
        self.last_loop_sequence = FLIGHT_LOOP_SEQUENCE

        # calculate relative to starting position
        self.last_position = new_position
        return new_position - self.starting_position


class TrueStateProducer(StateProducer):
    # noinspection PyMethodMayBeStatic
    def getState(self):
        # type: () -> object
        return True


class NotStateProducer(StateProducer):
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

    def reset(self):
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

    def reset(self):
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
            self.position = op(new_position, self.notch_size / 2)

        # done
        return int(self.position / self.notch_size)


class ClickProducer(object):
    def __init__(self, digital_input_producer):
        # type: (StateProducer) -> None
        self.digital_input_producer = digital_input_producer
        self.state = None  # type: Union[bool, None]
        self.first_press = None

    # get delta change
    def isClicked(self):

        new_state = self.digital_input_producer.getState()

        if new_state is None:
            return None

        if new_state == 0:
            if self.first_press is None:
                return False
            result =  time() - self.first_press < 0.2
            self.first_press = None
            return result
        else:
            if self.first_press is None:
                self.first_press = time()
            return 0


class Interaction(object):

    @staticmethod
    def _getPhidget(phidget):
        # type: ( str ) -> Phidget
        from PhidgetControlsConfig import PHIDGETS

        phidget_type, phidget_id = PHIDGETS[phidget]  # type: (type[Phidget], int)
        return get_phidget(phidget_type, phidget_id)

    def tick(self):
        pass


class If(Interaction):
    def __init__(self, state_producer, interaction):
        self.if_state_producer = self._getPhidget(state_producer)
        self.interaction = interaction

    def tick(self):
        if self.if_state_producer.getState():
            self.interaction.tick()


class Unless(Interaction):
    def __init__(self, state_producer, interaction):
        self.if_state_producer = self._getPhidget(state_producer)
        self.interaction = interaction

    def tick(self):
        if not self.if_state_producer.getState():
            self.interaction.tick()


class Rotate(Interaction):
    def __init__(self, position_producer_id, notch_size, xref, min_value, max_value, step):
        # type: (str, int, str, Number, Number, Number) -> None
        self.delta_producer = DeltaProducer(NotchedPositionProducer(
            RelativePositionProducer(self._getPhidget(position_producer_id)), notch_size))
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
    def __init__(self, position_producer, xref, digit):
        # type: (str, str, int) -> None
        self.delta_producer = DeltaProducer(NotchedPositionProducer(self._getPhidget(position_producer), 10))
        self.digit = digit
        self.ref = XPLMFindDataRef(xref)
        self.getter = XPLMGetDatai
        self.setter = XPLMSetDatai

    def tick(self):
        delta = self.delta_producer.getDelta()
        if not delta:
            return
        val = self.getter(self.ref)
        increment_digit = 10 ** (self.digit - 1)
        modulo = increment_digit * 10
        remainder = (val + delta * increment_digit) % modulo
        quotient = int(val / modulo) * modulo
        val = quotient + remainder
        self.setter(self.ref, val)


class SetValue(Interaction):

    def __init__(self, position_producer, xref, increment, min_value, max_value):
        # type: (Phidget, str, str, Number, Number, Number) -> None
        self.delta_producer = DeltaProducer(NotchedPositionProducer(self._getPhidget(position_producer), 10))
        self.increment = increment
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
        val = min(self.max, max(self.min, self.getter(self.ref) + delta * self.increment))
        self.setter(self.ref, val)


class Tune(Rotate):
    def __init__(self, position_producer_id, xref, min_value, max_value, inc):
        # type: (str, str, Number, Number, Number) -> None
        Rotate.__init__(self, position_producer_id, 10, xref, min_value, max_value, inc)


class SetHeading(Rotate):
    def __init__(self, position_producer_id, xref):
        # type: (str, str) -> None
        Rotate.__init__(self, position_producer_id, 2, xref, 0.0, 360.0, 1.0)


class SetBearing(Rotate):
    def __init__(self, position_producer_id, xref):
        # type: (str, str) -> None
        Rotate.__init__(self, position_producer_id, 2, xref, 0.0, 360.0, 1.0)


class Click(Interaction):
    def __init__(self, state_producer_id, xref):
        # type: (str, str) -> None
        self.click_producer = ClickProducer(self._getPhidget(state_producer_id))
        self.ref = XPLMFindCommand(xref)

    def tick(self):
        if self.click_producer.isClicked():
            XPLMCommandOnce(self.ref)


class UpDown(Interaction):
    def __init__(self, position_producer_id, up, down):
        # type: (str, str, str) -> None
        self.delta_producer = DeltaProducer(NotchedPositionProducer(self._getPhidget(position_producer_id), 20))
        self.up = XPLMFindCommand(up)
        self.down = XPLMFindCommand(down)

    def tick(self):
        delta = self.delta_producer.getDelta()
        if delta < 0:
            XPLMCommandOnce(self.up)
        if delta > 0:
            XPLMCommandOnce(self.down)


class Command(object):

    def __init__(self, key, description, triggered, plugin):
        # type: (str, str, callable, PythonInterface) -> None
        self.key = key
        self.triggered = triggered
        self.plugin = plugin
        self.cmd = XPLMCreateCommand("fscode/phidgetcontrols/" + key, description)
        self.callback = self.handle_callback
        logging.debug("Registering command for mode %s", self.key)
        XPLMRegisterCommandHandler(self.plugin, self.cmd, self.callback, 0, 0)

    def stop(self):
        logging.debug("Unregistering command for mode %s", self.key)
        XPLMUnregisterCommandHandler(self.plugin, self.cmd, self.callback, 0, 0)

    def handle_callback(self, _in_command, in_phase, _in_reference):
        if in_phase == 0:
            logging.debug('Triggering command %s', self.key)
            self.triggered()


# Plugin boilerplate
class PythonInterface:

    interactions = []  # type: List[ Interaction ]

    def __init__(self):
        self.Desc = None
        self.Sig = None
        self.Name = None
        self.commands = []
        self.interactions = []
        self.flight_loop = None

    def XPluginStart(self):

        logging.root.addHandler(XPlaneLogger())
        logging.root.setLevel(logging.DEBUG)

        # boilerplate
        self.Name = "PhidgetControls"
        self.Sig = "fscode.phidgets"
        self.Desc = (
            "Plug-in for controlling cockpit functions via Phidgets, for example "
            " radio frequencies on a Phidget Encoder knob.")

        logging.info("Plugin start")

        # set up commands for modes of interactions
        from PhidgetControlsConfig import INTERACTIONS
        for (k, d, i) in INTERACTIONS:
            self.commands.append(Command(k, d, lambda sk=k, si=i: self.setInteractions(sk, si), self))

        # hook-up into X loop
        logging.debug("Registering flight loop")
        # self.loop_callback = self.handle_loop
        _CreateFlightLoop_t = [1, self.handle_loop, 0]
        self.flight_loop = XPLMCreateFlightLoop(self, _CreateFlightLoop_t)
        XPLMScheduleFlightLoop(self, self.flight_loop, FLIGHT_LOOP_TIMER, 1)

        # complete
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        logging.info("Plugin stop")

        logging.debug("Unregistering flight loop")
        XPLMDestroyFlightLoop(self, self.flight_loop)

        logging.debug("Close phidgets")
        close_all_phidgets()

        logging.debug("Unregistering commands")
        for command in self.commands:
            command.stop()

    # noinspection PyMethodMayBeStatic
    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, _in_from, _in_message, _in_param):
        pass

    def handle_loop(self, _elapsed_me, _elapsed_sim, _counter, _reference):

        global FLIGHT_LOOP_SEQUENCE
        FLIGHT_LOOP_SEQUENCE += 1

        # open all phidgets
        ensure_phidgets_opened()

        # go through interactions
        try:
            for interaction in self.interactions:
                interaction.tick()
        except PhidgetException as phidget_exception:
            log_phidget_exception(phidget_exception)
        except Exception as exception:
            logging.exception(exception)

        # continue
        return FLIGHT_LOOP_TIMER

    def setInteractions(self, mode, new_interactions):
        # type: (str, List[Interaction]) -> None
        logging.debug("Setting interactions for %s", mode)
        self.interactions = new_interactions
