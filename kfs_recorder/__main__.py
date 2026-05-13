import sys
from time import sleep

import readkeys
from pylsl import StreamInfo, StreamOutlet, local_clock

from . import ForceSensorSerial, __version__
from ._settings import Settings


def run():
    cfg = Settings("settings.toml")
    print(cfg.dict)

    if cfg.lsl: # LSL support
        info = StreamInfo(cfg.lsl_name, 'Force', channel_count=2, nominal_srate=100)
        outlet = StreamOutlet(info)
        print("LSL stream created: ", info.name())
    else:
        outlet = None

    sensor = ForceSensorSerial(cfg.serial_port, filename=cfg.output_file)
    sensor.start()
    readkeys.flush()

    if cfg.recording_delay>0:
        sleep(cfg.recording_delay)
        # clear sensor cache
        while True:
            data = sensor.poll()
            if len(data) == 0:
                break

    print(f"recording from {sensor.port} \n")
    k = ""
    while True:
        data = sensor.poll()
        if len(data) > 0:
            if isinstance(outlet, StreamOutlet):
                for x in data:
                    outlet.push_sample([x.time, x.val])

            if cfg.display :
                x = data[-1]
                sys.stdout.write(f"trigger: {x.csv()}      \r")

        k = readkeys.getch(NONBLOCK = True)
        if k == "b":
            sensor.set_baseline()
        elif k == "t":
            sensor.send_trigger(255)
        elif k == "q":
            break

    print()
    sensor.stop()
    sensor.save()


if __name__ == "__main__":

    if sys.version_info[0] != 3 or sys.version_info[1] < 10:
        raise RuntimeError("{} {} ".format("KFS recorder", __version__) +
                            "is not compatible with Python {0}.{1}.".format(
            sys.version_info[0],
            sys.version_info[1]) +
            "\n\nPlease use Python 3.10 or higher.")

    run()
