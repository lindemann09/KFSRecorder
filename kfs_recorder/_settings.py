from pathlib import Path
from typing import Dict

import tomllib


class Settings:

    def __init__(self, toml_filename:str|Path):
        try:
            with open(toml_filename, 'rb') as fl:
                d = tomllib.load(fl)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Configuration file '{toml_filename}' not found.") from exc
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Error decoding TOML file: {e}") from e

        self.serial_port = d.get("serial_port", "/dev/ttyUSB0")
        self.recording_delay = d.get("recording_delay", 0)
        self.output_file = d.get("output_file", "")
        self.display = d.get("display", True)
        self.lsl = d.get("lsl", False)
        self.lsl_name = d.get("lsl_name", "ForceSensor")
        self.dict:Dict = d


    def get(self, key: str, default=None):
        return self.dict.get(key, default)