import atexit
from datetime import datetime
from typing import List

import serial

from ._time_stamped_data import TSData, TSFloat, TSInt


class ForceSensor(object):
    """ """

    def __init__(self, port,
                 baudrate=115200,
                 filename: str | None = None,
                 init_time: int | None = None) -> None:

        self.port = port
        self.baudrate = baudrate
        self.serial_port = None
        if isinstance(init_time, int):
            TSData.set_init_time(init_time)

        self._poll_cache: bytes = b""
        self._n_returned_data = 0
        self._baseline = 0
        self._data: List[TSFloat] = []
        self._trigger: List[TSInt] = []

        self.filename = filename
        if filename is not None and len(filename) > 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(filename, "w", encoding="utf-8") as fl:
                fl.write(f"# Krakow sensor force: {now}\n")

        atexit.register(self.stop)
        atexit.register(self.save)

    def set_baseline(self, last_n_samples:int=5):
        last_vals = [x.val for x in self._data[(-1*last_n_samples):]]
        bsl = sum(last_vals) / len(last_vals)
        self._baseline += bsl

    def start(self, timeout: float = 0):
        if self.serial_port is None:
            self.serial_port = serial.Serial(self.port,
                baudrate=self.baudrate, timeout=timeout)

    def stop(self):
        if self.serial_port is not None:
            self.serial_port.close()
            self.serial_port = None

    def n_trigger(self):
        return len(self._trigger)

    def n_samples(self):
        return len(self._data)

    def send_trigger(self, tr:int):
        self._trigger.append(TSInt(tr))

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
                    d = TSFloat(float(dat.decode()) - self._baseline)
                    self._data.append(d)

            else:
                # no data in cue: return data
                if len(self._data) > self._n_returned_data:
                    rtn = self._data[self._n_returned_data :]
                    self._n_returned_data = len(self._data)
                    return rtn
        return []

    def save(self):
        if self.filename is not None:
            with open(self.filename, "a+", encoding="utf-8") as fl:
                #write trigger
                for tr in self._trigger:
                    fl.write("#tr, " + tr.csv() + "\n")

                for dat in self._data:
                    if len(self._trigger) > 0 and self._trigger[0].time <= dat.time:
                        tr = self._trigger.pop(0).val
                    else:
                        tr = 0
                    fl.write(dat.csv(extra_column=tr) + "\n")

            self._data: List[TSFloat] = []
            self._trigger: List[TSInt] = []
