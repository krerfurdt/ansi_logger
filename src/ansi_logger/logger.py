from __future__ import annotations

import logging
import sys

from typing_extensions import Unpack
from typing import Any

from ._types import LoggerConfig
from .formatters import DEFAULT_FORMAT_STRING, FileFormatter, StreamFormatter
from .filesystem import FileStreamer
from .handlers import HandlerFactory, HandlerLease

class Logger:
    def __init__(self, **kwargs: Unpack[LoggerConfig]):
        self.file_handler = None
        self.console_stream_handler = None
        self.file_stream_handler = None
        self.color_formatter = None
        self.file_formatter = None
        self.stream_formatter = None
        self.logger = None
        self._handler_factory = HandlerFactory()
        self._handler_leases: list[HandlerLease] = []
        self._closed = False
        self._initialize_logger(**kwargs)

    def _initialize_logger(self, **kwargs: Any):
        console_only = kwargs.get('console_only', False)
        file_only = kwargs.get('file_only', False)
        if console_only and file_only:
            raise ValueError("Cannot specify both console_only and file_only as True")
        try:
            if console_only:
                self._initialize_console(**kwargs)
            elif file_only:
                self._initialize_file_stream(**kwargs)
            else:
                self._initialize_file_stream(**kwargs)
                self._attach_console(**kwargs)
        except Exception as e:
            self.close()
            raise RuntimeError(f"Failed to initialize logger: {e}") from e

    def _initialize_console(self, **kwargs: Any):
        try:
            stream = kwargs.pop('stream', sys.stderr)
            level = kwargs.get('level', logging.INFO)
            self.logger = logging.getLogger(kwargs.get('name', 'ANSI.logger.console'))
            self.logger.setLevel(level)
            self.logger.propagate = False
            kwargs['tty_required'] = False
            lease = self._handler_factory.acquire_console_handler(self.logger, stream=stream, **kwargs)
            if lease is not None:
                self.console_stream_handler = lease.handler
                self._handler_leases.append(lease)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize console logger: {e}") from e

    def _attach_console(self, **kwargs: Any):
        try:
            if self.logger is None:
                return
            if self.file_handler is None:
                return
            if self.file_stream_handler is None:
                return
            lease = self._handler_factory.acquire_console_handler(self.logger, **kwargs)
            if lease is not None:
                self.console_stream_handler = lease.handler
                self._handler_leases.append(lease)
        except Exception as e:
            raise RuntimeError(f"Failed to attach console logger: {e}") from e

    def _initialize_file_stream(self, **kwargs: Any):
        try:
            level = kwargs.get('level', logging.INFO)
            self.file_handler = FileStreamer(**kwargs)
            kwargs['file_handler'] = self.file_handler
            self.logger = logging.getLogger(self.file_handler.log_file_name)
            self.logger.setLevel(level)
            self.logger.propagate = False
            lease = self._handler_factory.acquire_file_handler(self.logger, **kwargs)
            if lease is not None:
                self.file_stream_handler = lease.handler
                self._handler_leases.append(lease)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize file logger: {e}") from e

    def _set_debug(self,flag: bool):
        level = logging.DEBUG if flag else logging.INFO
        self.tag_debug = flag
        if self.logger is not None:
            self.logger.setLevel(level)
        self._handler_factory.set_debug_for_leases(self._handler_leases, flag)
        for lease in self._handler_leases:
            lease.handler.setLevel(level)

    def close(self):
        if self._closed:
            return
        self._handler_factory._release_leases(self._handler_leases)
        self._handler_leases.clear()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def info(self, msg, *args, **kwargs):
        kwargs.setdefault('stacklevel', 2)
        self.logger.info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        kwargs.setdefault('stacklevel', 2)
        self.logger.error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        kwargs.setdefault('stacklevel', 2)
        self.logger.warning(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        kwargs.setdefault('stacklevel', 2)
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        kwargs.setdefault('stacklevel', 2)
        if 'exc_info' not in kwargs or kwargs['exc_info'] is True:
            exc_info = sys.exc_info()
            kwargs['exc_info'] = False if exc_info[0] is None else exc_info
        self.logger.error(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        kwargs.setdefault('stacklevel', 2)
        self.logger.debug(msg, *args, **kwargs)
