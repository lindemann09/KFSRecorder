import atexit
from datetime import datetime
from typing import List

from pylsl import StreamOutlet

from ._time_stamped_data import TSData, TSFloat, TSInt


class ForceSensor(object):
    """ """

    def __init__(self,
                 filename: str | None = None,
                 init_time: int | None = None,
                 lsl_stream: StreamOutlet | None = None) -> None:

        if isinstance(init_time, int):
            TSData.set_init_time(init_time)

        self._baseline = 0
        self._data: List[TSFloat] = []
        self._trigger: List[TSInt] = []
        self._lsl_stream = lsl_stream

        self.filename = filename
        if filename is not None and len(filename) > 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(filename, "w", encoding="utf-8") as fl:
                fl.write(f"# Force sensor data: {now}\n")

        atexit.register(self.save)

    def set_baseline(self, last_n_samples:int=5):
        last_vals = [x.val for x in self._data[(-1*last_n_samples):]]
        bsl = sum(last_vals) / len(last_vals)
        self._baseline += bsl

    def n_trigger(self):
        return len(self._trigger)

    def n_samples(self):
        return len(self._data)

    def new_trigger(self, tr:int):
        dat = TSInt(tr)
        self._trigger.append(dat)
        if isinstance(self._lsl_stream, StreamOutlet):
            self._lsl_stream.push_sample([dat.val])

    def new_data(self, val: float, consider_baseline: bool = True):

        if consider_baseline:
            dat = TSFloat(val - self._baseline)
        else:
            dat = TSFloat(val)

        self._data.append(dat)
        if isinstance(self._lsl_stream, StreamOutlet):
            self._lsl_stream.push_sample([dat.val])

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
