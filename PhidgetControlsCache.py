import logging
import time
from typing import Dict

from Phidget22.ErrorCode import ErrorCode
from Phidget22.Phidget import Phidget
from Phidget22.PhidgetException import PhidgetException

IGNORE_PHIDGET_ERROR = [ErrorCode.EPHIDGET_NOTATTACHED, ErrorCode.EPHIDGET_UNKNOWNVAL]  # type: [int]

_phidgets = {}  # type: Dict[ (type[Phidget], int), Phidget]
_last_ensure_open = 0


def get_phidget(phidget_type, phidget_id):
    # type: ( type[Phidget], int) -> Phidget
    key = (phidget_type, phidget_id)
    if key in _phidgets:
        return _phidgets[key]

    phidget = phidget_type()  # type: Phidget
    phidget.setDeviceSerialNumber(phidget_id)
    _phidgets[key] = phidget

    log_phidget(phidget, 'Instantiated')

    return phidget


def close_all_phidgets():
    # type: () -> None
    for key, phidget in _phidgets.iteritems():
        try:
            log_phidget(phidget, 'Closing')
            phidget.close()
        except PhidgetException:
            pass
    _phidgets.clear()


def ensure_phidgets_opened():
    # type: () -> None

    # wait for at least 1s between attempts
    if time.time() - _last_ensure_open < 1:
        return
    _open_retry_timer = time.time()

    for phidget in _phidgets.values():
        # is the phidget attached?
        if not phidget.getAttached():

            # try to open/attach
            try:
                log_phidget(phidget, "Opening")
                phidget.open()
            except PhidgetException, e:
                log_phidget_exception(e)


def log_phidget_exception(e):
    # type: (PhidgetException) -> None
    if e.code in IGNORE_PHIDGET_ERROR:
        return
    logging.info('%s (%i)', e.description, e.code)


def log_phidget(phidget, message):
    # type: (Phidget, str) -> None
    class_name = phidget.__class__.__name__
    logging.debug('Phidget %s#%i: %s', class_name, phidget.getDeviceSerialNumber(),  message)
