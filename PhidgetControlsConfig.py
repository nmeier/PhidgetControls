from typing import Callable, List, Dict
from Phidget22 import Phidget
from Phidget22.Devices.Encoder import Encoder
from Phidget22.Devices.DigitalInput import DigitalInput
from PI_PhidgetControls import Interaction, Tune, Click, SetBearing, SetDigit, SetHeading, SetValue

# Configuration: phidgets and interactions
PHIDGETS = {
    'E1': (Encoder, 82081),
    'E2': (Encoder, 82141),
    'D1': (DigitalInput, 82081),
    'D2': (DigitalInput, 82141)
}  # type: Dict[str, (type[Phidget], int)]

INTERACTIONS = {
    'COM1': lambda: [
        Tune('E1', 'sim/cockpit2/radios/actuators/com1_standby_frequency_Mhz', 118, 137, 1),
        Tune('E2', 'sim/cockpit2/radios/actuators/com1_standby_frequency_khz', 0, 1000, 10),
        Click('D1', 'sim/radios/com1_standy_flip'),
        Click('D2', 'sim/radios/stby_com1_fine_up_833')],
    'NAV1': lambda: [
        Tune('E1', 'sim/cockpit2/radios/actuators/nav1_standby_frequency_Mhz', 108, 117, 1),
        Tune('E2', 'sim/cockpit2/radios/actuators/nav1_standby_frequency_khz', 0, 95, 10),
        Click('D1', 'sim/radios/nav1_standy_flip')],
    'NAV2': lambda: [
        Tune('E1', 'sim/cockpit2/radios/actuators/nav2_standby_frequency_Mhz', 108, 117, 1),
        Tune('E2', 'sim/cockpit2/radios/actuators/nav2_standby_frequency_khz', 0, 95, 10),
        Click('D1', 'sim/radios/nav2_standy_flip')],
    'OBS': lambda: [
        SetBearing('E1', 'sim/cockpit/radios/nav1_obs_degm'),
        SetBearing('E2', 'sim/cockpit/radios/nav2_obs_degm')],
    'ADF': lambda: [
        SetValue('E1', 'D1', 'sim/cockpit2/radios/actuators/adf1_standby_frequency_hz', 100, 1000, 0, 9999),
        SetValue('E2', 'D2', 'sim/cockpit2/radios/actuators/adf1_standby_frequency_hz', 1, 10, 0, 9999),
        Click('D1', 'sim/radios/adf1_standy_flip')],
    'ADFCARD': lambda: [
        SetBearing('E1', 'sim/cockpit/radios/adf1_cardinal_dir')],
    'QNH': lambda: [
        SetValue('E1', None, 'sim/cockpit/misc/barometer_setting', 0.01, None, 27.90, 31.50)],
    'TRANSPONDER': lambda: [
        SetDigit('E1', 'D1', 'sim/cockpit2/radios/actuators/transponder_code', 4),
        SetDigit('E1', '!D1', 'sim/cockpit2/radios/actuators/transponder_code', 3),
        SetDigit('E2', 'D2', 'sim/cockpit2/radios/actuators/transponder_code', 2),
        SetDigit('E2', '!D2', 'sim/cockpit2/radios/actuators/transponder_code', 1)],
    'APHDG': lambda: [
        SetHeading('E1', 'sim/cockpit/autopilot/heading_mag'),
        SetHeading('E2', 'sim/cockpit/gyros/dg_drift_vac_deg')],
    'APVERTICALS': lambda: [
        SetValue('E1', 'D1', 'sim/cockpit/autopilot/altitude', 100.0, 1000, 0, 56000),
        SetValue('E2', None, 'sim/cockpit/autopilot/vertical_velocity', 100.0, 100.0, -2500, 2500)]
}  # type: Dict[str, Callable[[], List[Interaction]]]
