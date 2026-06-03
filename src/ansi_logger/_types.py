# src/ansi_logger/_types.py

from __future__ import annotations

from os import PathLike
from typing import Literal, Sequence, TextIO, TypeAlias, TypedDict


LogLevel: TypeAlias = int | str
PathLikeStr: TypeAlias = str | PathLike[str]


AnsiForegroundColor: TypeAlias = Literal[
    "FG_BLACK",
    "FG_RED",
    "FG_GREEN",
    "FG_YELLOW",
    "FG_BLUE",
    "FG_MAGENTA",
    "FG_CYAN",
    "FG_WHITE",
]

AnsiBackgroundColor: TypeAlias = Literal[
    "BG_BLACK",
    "BG_RED",
    "BG_GREEN",
    "BG_YELLOW",
    "BG_BLUE",
    "BG_MAGENTA",
    "BG_CYAN",
    "BG_WHITE",
]

AnsiStyle: TypeAlias = Literal[
    "BOLD",
    "DIM",
    "ITALIC",
    "UNDERLINE",
    "BLINK",
    "FAST_BLINK",
    "REVERSE",
    "HIDDEN",
    "STRIKETHROUGH",
]

AnsiResetType: TypeAlias = Literal[
    "FG",
    "BG",
    "ALL",
]


class AnsiFormatOptions(TypedDict, total=False):
    fg_color: AnsiForegroundColor | None
    bg_color: AnsiBackgroundColor | None
    styles: Sequence[AnsiStyle] | None
    reset: AnsiResetType
    debug: bool


class LoggerConfig(TypedDict, total=False):
    name: str
    log_dir: PathLikeStr
    log_file: str

    console_only: bool
    file_only: bool
    stream: TextIO

    level: LogLevel
    max_bytes: int
    backup_count: int
    encoding: str

    debug: bool
    ensure_ascii: bool