from typing import Callable, List, Dict
from Phidget22 import Phidget
from Phidget22.Devices.Encoder import Encoder
from Phidget22.Devices.DigitalInput import DigitalInput
from PI_PhidgetControls import Interaction, Tune, Click, SetBearing, SetDigits, SetHeading, SetValue

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
    'OBS1': lambda: [
        SetBearing('E1', 'sim/cockpit/radios/nav1_obs_degm')],
    'NAV2': lambda: [
        Tune('E1', 'sim/cockpit2/radios/actuators/nav2_standby_frequency_Mhz', 108, 117, 1),
        Tune('E2', 'sim/cockpit2/radios/actuators/nav2_standby_frequency_khz', 0, 95, 10),
        Click('D1', 'sim/radios/nav2_standy_flip')],
    'OBS2': lambda: [
        SetBearing('E1', 'sim/cockpit/radios/nav2_obs_degm')],
    'ADF1': lambda: [
        SetDigits('E1', 'D1', 'sim/cockpit2/radios/actuators/adf1_standby_frequency_hz', 100, 1000, 10000),
        SetDigits('E2', 'D2', 'sim/cockpit2/radios/actuators/adf1_standby_frequency_hz', 1, 10, 100),
        Click('D1', 'sim/radios/adf1_standy_flip')],
    'ADFCARD': lambda: [
        SetBearing('E1', 'sim/cockpit/radios/adf1_cardinal_dir')],
    'HDG': lambda: [
        SetHeading('E1', 'sim/cockpit/autopilot/heading_mag'),
        SetHeading('E2', 'sim/cockpit/gyros/dg_drift_vac_deg')],
    'QNH': lambda: [
        SetValue('E1', 'sim/cockpit/misc/barometer_setting', 0.01, 27.90, 31.50)],
    'TRANSPONDER': lambda: [
        SetDigits('E1', 'D1', 'sim/cockpit2/radios/actuators/transponder_code', 100, 1000, 10000),
        SetDigits('E2', 'D2', 'sim/cockpit2/radios/actuators/transponder_code', 1, 10, 100),
        Click('D1', 'sim/transponder/transponder_ident')],
    'APVV': lambda: [
        SetValue('E1', 'sim/cockpit/autopilot/vertical_velocity', 100.0, -2000, 2000)]
}  # type: Dict[str, Callable[[], List[Interaction]]]
