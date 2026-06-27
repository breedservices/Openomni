from __future__ import annotations

from logging import (
    INFO,
    Filter,
    Logger,
    LogRecord,
    getLogger,
)

from coloredlogs import install as InstallLogs

Bold = {"bold": True}

LevelStyles = {
    "critical": {"bold": True, "color": "red"},
    "error": {"bold": True, "color": "red"},
    "warning": {"bold": True, "color": "yellow"},
    "notice": {"bold": True, "color": "magenta"},
    "info": {"bold": True, "color": "green"},
    "debug": {"bold": True, "color": "cyan"},
    "spam": {"bold": True, "color": "green"},
    "verbose": {"bold": True, "color": "blue"},
}

FieldStyles = {
    "ram": {"bold": True, "color": "cyan"},
    "filename": {"bold": True, "color": "magenta"},
    "levelname": {"bold": True},
    "message": {"bold": True},
}


class RamInject(Filter):
    __slots__ = ()

    def filter(self, Record: LogRecord) -> bool:
        Record.ram = _RamUsage()
        return True


def _RamUsage() -> str:
    from psutil import Process

    Mb = Process().memory_info().rss / 1048576
    return f"{Mb:.1f}MB"


def SetupLog(Level: int = INFO) -> Logger:
    Root = getLogger()
    InstallLogs(
        level=Level,
        logger=Root,
        fmt="%(ram)s; %(filename)s: %(levelname)s %(message)s",
        level_styles=LevelStyles,
        field_styles=FieldStyles,
    )
    for Handler in Root.handlers:
        Handler.addFilter(RamInject())
    return getLogger("omni")
