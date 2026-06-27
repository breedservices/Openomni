from msgspec import Struct, field
from msgspec.json import Decoder


class Cfg(Struct, frozen=True):
    Token: str = field(name="TOKEN")
    DatabaseFile: str = field(name="DATABASE_FILE")


_Decoder = Decoder(Cfg)


def LoadConfig(FilePath: str) -> Cfg:
    with open(FilePath, "rb") as f:
        return _Decoder.decode(f.read())
