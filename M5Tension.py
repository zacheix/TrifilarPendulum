from Phidget22.PhidgetException import *
from Phidget22.Phidget import *
from Phidget22.Devices.Log import *
from Phidget22.LogLevel import *
from Phidget22.Devices.VoltageRatioInput import *
import time

# Enable logging once at import time
Log.enable(LogLevel.PHIDGET_LOG_INFO, "phidgetlog.log")

# Global dictionary to store latest readings
_latest_readings = {}

#-----------------------------------------------------------
# Event Handlers
#-----------------------------------------------------------
def onVoltageRatioChange(self, voltageRatio):
    channel = self.getChannel()
    _latest_readings[channel] = voltageRatio

def onAttach(self):
    print(f"Attach [Channel {self.getChannel()}]!")

def onDetach(self):
    print(f"Detach [Channel {self.getChannel()}]!")

def onError(self, code, description):
    print(f"Error on Channel {self.getChannel()}: Code {code} - {description}")

#-----------------------------------------------------------
# Module Functions
#-----------------------------------------------------------
def setup_tension_cells(serial_number, channels=1, timeout=5000):
    """
    Initializes and opens the specified number of VoltageRatioInput channels.
    """
    cells = []
    for ch in range(channels):
        try:
            cell = VoltageRatioInput()
            cell.setDeviceSerialNumber(serial_number)
            cell.setChannel(ch)
            cell.setOnVoltageRatioChangeHandler(onVoltageRatioChange)
            cell.setOnAttachHandler(onAttach)
            cell.setOnDetachHandler(onDetach)
            cell.setOnErrorHandler(onError)
            cell.openWaitAttachment(timeout)
            cells.append(cell)
        except PhidgetException as ex:
            print(f"Error initializing tension cell on channel {ch} (SN: {serial_number}): {ex}")
    return cells

def get_latest_forces():
    """
    Returns a copy of the latest raw voltage ratio readings.
    """
    return dict(_latest_readings)


def close_tension_cells(cells):
    """
    Closes all provided VoltageRatioInput channels.
    """
    for cell in cells:
        try:
            cell.close()
        except PhidgetException as ex:
            print(f"Error closing channel {cell.getChannel()}: {ex}")
