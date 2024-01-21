from typing import Dict, Tuple, List
from Phidget22 import Phidget
from Phidget22.Devices.Encoder import Encoder
from Phidget22.Devices.DigitalInput import DigitalInput
from PI_PhidgetControls import Interaction, Tune, Click, SetBearing, SetDigit, SetHeading, \
    SetValue, UpDown, If, Unless

# Configuration: phidgets and interactions
PHIDGETS = {
    'E1': (Encoder, 82081),
    'E2': (Encoder, 82141),
    'D1': (DigitalInput, 82081),
    'D2': (DigitalInput, 82141)
}  # type: Dict[str, (type[Phidget], int)]

INTERACTIONS = [
    ('COM1', 'COM1 Frequency Mhz (flip standby) and Khz (fine up)', [
        Tune('E1', 'sim/cockpit2/radios/actuators/com1_standby_frequency_Mhz', 118, 137, 1),
        Tune('E2', 'sim/cockpit2/radios/actuators/com1_standby_frequency_khz', 0, 1000, 10),
        Click('D1', 'sim/radios/com1_standy_flip'),
        Click('D2', 'sim/radios/stby_com1_fine_up_833')]),
    ('NAV1', 'NAV1 Frequency Mhz (flip standby) and Khz', [
        Tune('E1', 'sim/cockpit2/radios/actuators/nav1_standby_frequency_Mhz', 108, 117, 1),
        Tune('E2', 'sim/cockpit2/radios/actuators/nav1_standby_frequency_khz', 0, 95, 10),
        Click('D1', 'sim/radios/nav1_standy_flip')]),
    ('NAV2', 'NAV2 Frequency Mhz (flip standby) and Khz', [
        Tune('E1', 'sim/cockpit2/radios/actuators/nav2_standby_frequency_Mhz', 108, 117, 1),
        Tune('E2', 'sim/cockpit2/radios/actuators/nav2_standby_frequency_khz', 0, 95, 10),
        Click('D1', 'sim/radios/nav2_standy_flip')]),
    ('OBS', 'OBS Degree Nav1 and Nav2', [
        SetBearing('E1', 'sim/cockpit/radios/nav1_obs_degm'),
        SetBearing('E2', 'sim/cockpit/radios/nav2_obs_degm')]),
    ('ADF', 'ADF Frequency 100 (flip standby) and 10', [
        Unless('D1', SetValue('E1', 'sim/cockpit2/radios/actuators/adf1_standby_frequency_hz', 100, 0, 9999)),
        If('D1', SetValue('E1', 'sim/cockpit2/radios/actuators/adf1_standby_frequency_hz', 1000, 0, 9999)),
        Unless('D2', SetValue('E2', 'sim/cockpit2/radios/actuators/adf1_standby_frequency_hz', 1, 0, 9999)),
        If('D2', SetValue('E2', 'sim/cockpit2/radios/actuators/adf1_standby_frequency_hz', 10, 0, 9999)),
        Click('D1', 'sim/radios/adf1_standy_flip')]),
    ['ADFCARD', 'ADF Card', (
        SetBearing('E1', 'sim/cockpit/radios/adf1_cardinal_dir'))],
    ['QNH', 'Barometer', (
        SetValue('E1', 'sim/cockpit/misc/barometer_setting', 0.01, 27.90, 31.50))],
    ('TRANSPONDER', 'Transponder', [
        Unless('D1', SetDigit('E1', 'sim/cockpit2/radios/actuators/transponder_code', 4)),
        If('D1', SetDigit('E1', 'sim/cockpit2/radios/actuators/transponder_code', 3)),
        Unless('D2', SetDigit('E2', 'sim/cockpit2/radios/actuators/transponder_code', 2)),
        If('D2', SetDigit('E2', 'sim/cockpit2/radios/actuators/transponder_code', 1))]),
    ('HDG', 'Heading Degree (AP follow) and Drift Degree (AP hold)', [
        SetHeading('E1', 'sim/cockpit/autopilot/heading_mag'),
        SetHeading('E2', 'sim/cockpit/gyros/dg_drift_vac_deg'),
        Click('D1', 'sim/autopilot/heading'),
        Click('D1', 'sim/autopilot/heading_hold')]),
    ('APLATERAL', 'Autopilot Heading (follow) and Nav1 (track)', [
        SetHeading('E1', 'sim/cockpit/autopilot/heading_mag'),
        SetHeading('E2', 'sim/cockpit/radios/nav1_obs_degm'),  # sim/cockpit/gyros/dg_drift_vac_deg
        Click('D1', 'sim/autopilot/heading'),  # sim/autopilot/heading_hold
        Click('D2', 'sim/autopilot/NAV')]),
    ('APALTITUDE', 'Autopilot Altitude 1000 (follow) and 100 (sync)', [
        SetValue('E1', 'sim/cockpit/autopilot/altitude', 1000.0, 0, 56000),
        SetValue('E2', 'sim/cockpit/autopilot/altitude', 100.0, 0, 56000),
        Click('D1', 'sim/autopilot/altitude_hold'),
        Click('D2', 'sim/autopilot/altitude_sync')]),
    ('APVERTICAL', 'Autopilot Vertical Velocity 1000 (follow) and 100 (hold current)', [
        SetValue('E1', 'sim/cockpit/autopilot/vertical_velocity', 1000.0, -2500, 2500),
        SetValue('E2', 'sim/cockpit/autopilot/vertical_velocity', 100.0, -2500, 2500),
        Click('D1', 'sim/autopilot/vertical_speed_pre_sel'),
        Click('D2', 'sim/autopilot/vertical_speed')]),
    ('GARMIN530', 'Garmin 530', [
        Unless('D2', UpDown('E2', 'sim/GPS/g430n1_chapter_up', 'sim/GPS/g430n1_chapter_dn')),
        If('D2', UpDown('E2', 'sim/GPS/g430n1_page_up', 'sim/GPS/g430n1_page_dn')),
        Click('D1', 'sim/GPS/g430n1_chapter_up'),
        Click('D2', 'sim/GPS/g430n1_chapter_dn')])
]  # type: List[ Tuple[str, str, List[Interaction]]]
