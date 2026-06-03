# src/ansi_logger/__init__.py

from .ansi import AnsiFormatter
from .filesystem import APP_NAME, FileStreamer
from .formatters import DEFAULT_FORMAT_STRING, FileFormatter, StreamFormatter
from .logger import Logger
from ._types import AnsiBackgroundColor, AnsiForegroundColor, AnsiFormatOptions, AnsiResetType, AnsiStyle, LoggerConfig

print = AnsiFormatter.print

__all__ = [
    "APP_NAME",
    "AnsiFormatter",
    "FileFormatter",
    "FileStreamer",
    "Logger",
    "LoggerConfig",
    "AnsiFormatOptions",
    "AnsiForegroundColor",
    "AnsiBackgroundColor",
    "AnsiStyle",
    "AnsiResetType",
    "StreamFormatter",
    "DEFAULT_FORMAT_STRING",
    "print",
]