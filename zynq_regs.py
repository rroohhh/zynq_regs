from pathlib import Path
import dataclasses
from dataclasses import dataclass
import json
from typing import *

class DataclassJSON:
    _dataclass_types = []

    def register(cls):
        class Wrapped(cls):
            def _tryfromdict(values):
                try:
                    return Wrapped(**values)
                except Exception as e:
                    return None

        DataclassJSON._dataclass_types.append(Wrapped)
        return Wrapped

    def decode_hook(dct):
        for ty in DataclassJSON._dataclass_types:
            if (parsed := ty._tryfromdict(dct)) is not None:
                return parsed
        return dct

    class encoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)


@DataclassJSON.register
@dataclass
class Register:
    addr: int
    mask: int
    name: str
    uniqueid: str
    description: str
    bit_start: int
    bit_end: int

def load_registers(path: str = "data/regs.json") -> Dict[str, Register]:
    return json.loads(Path(path).read_text(), object_hook=DataclassJSON.decode_hook)
# print(json.dumps(a, indent=4, sort_keys=True, cls=DataclassJSON.encoder))
