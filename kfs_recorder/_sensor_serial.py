import atexit
from typing import List

import serial
from pylsl import StreamOutlet

from ._sensor import ForceSensor
from ._time_stamped_data import TSFloat


class ForceSensorSerial(ForceSensor):
    """ """

    def __init__(self, port,
                 baudrate=115200,
                 filename: str | None = None,
                 init_time: int | None = None,
                 lsl_stream: StreamOutlet | None = None) -> None:

        super().__init__(filename=filename, init_time=init_time, lsl_stream=lsl_stream)
        self.port = port
        self.baudrate = baudrate
        self.serial_port = None

        self._poll_cache: bytes = b""
        self._n_returned_data = 0

        atexit.register(self.stop)

    def start(self, timeout: float = 0):
        if self.serial_port is None:
            self.serial_port = serial.Serial(self.port,
                baudrate=self.baudrate, timeout=timeout)

    def stop(self):
        if self.serial_port is not None:
            self.serial_port.close()
            self.serial_port = None

    def poll(self) -> List[TSFloat]:
        """polls data and returns all available values.
        if block = false (default), it returns [] immediately, if no data is
        available yet, otherwise it wait until new data is available.
        """

        if self.serial_port is not None:
            dat = self.serial_port.read_until(size=15)
            if len(dat) > 0:
                if dat[-1] != 10:
                    # not all data are available yet
                    self._poll_cache += dat
                    return self.poll()
                else:
                    # last byte was a  "\n"
                    if len(self._poll_cache) > 0:
                        dat = self._poll_cache + dat
                        self._poll_cache = b"" # clear
                    self.new_data(float(dat.decode()), consider_baseline=True)
            else:
                # no data in cue: return data
                if len(self._data) > self._n_returned_data:
                    rtn = self._data[self._n_returned_data :]
                    self._n_returned_data = len(self._data)
                    return rtn
        return []
