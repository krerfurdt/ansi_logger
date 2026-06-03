from __future__ import annotations
import logging
import logging.handlers
import sys
import threading
from dataclasses import dataclass
from typing import Callable
from .formatters import StreamFormatter, FileFormatter
from .filesystem import FileStreamer

HandlerKey = tuple[str, type[logging.Handler], str]

@dataclass(frozen=True)
class HandlerLease:
    key: HandlerKey
    logger: logging.Logger
    handler: logging.Handler

@dataclass
class _RegistryEntry:
    logger: logging.Logger
    handler: logging.Handler
    refs: int

class HandlerRegistry:
    _entries: dict[HandlerKey, _RegistryEntry] = {}
    _lock = threading.RLock()

    @classmethod
    def make_key(cls, logger: logging.Logger, handler_type: type[logging.Handler], target: str) -> HandlerKey:
        return (logger.name, handler_type, str(target))

    @classmethod
    def acquire(cls, **kwargs) -> HandlerLease:
        logger: logging.Logger = kwargs.get('logger')
        if logger is None:
            raise ValueError("Logger must be provided to acquire a handler lease")
        file_handler: FileStreamer = kwargs.get('file_handler', None)
        if file_handler is None:
            target: str = kwargs.get('target', 'ANSI.Logger')
        else:
            target = file_handler.log_file_path
        handler_type: type[logging.Handler] = kwargs.get('handler_type')
        factory: Callable[[], logging.Handler] = kwargs.get('factory')
        if handler_type is None or factory is None:
            raise ValueError("Handler type and factory must be provided to acquire a handler lease")
        key = cls.make_key(logger, handler_type, target)
        with cls._lock:
            entry = cls._entries.get(key)
            if entry is None:
                handler = factory(**kwargs)
                handler._ansi_logger_target = str(target)
                handler._ansi_logger_shared = True
                logger.addHandler(handler)
                entry = _RegistryEntry(
                    logger=logger,
                    handler=handler,
                    refs=1
                )
                cls._entries[key] = entry
            else:
                entry.refs += 1
                handler = entry.handler
                if handler not in entry.logger.handlers:
                    entry.logger.addHandler(handler)
            return HandlerLease(
                key=key,
                logger=entry.logger,
                handler=entry.handler
            )

    @classmethod
    def release(cls, lease: HandlerLease) -> None:
        with cls._lock:
            entry = cls._entries.get(lease.key)
            if entry is None:
                return
            entry.refs -= 1
            if entry.refs > 0:
                return
            logger = entry.logger
            handler = entry.handler
            try:
                if handler in logger.handlers:
                    logger.removeHandler(handler)
                try:
                    handler.flush()
                finally:
                    handler.close()
            finally:
                cls._entries.pop(lease.key, None)

class HandlerFactory():
    def __init__(self):
        self._registry = HandlerRegistry()

    def _release_leases(self, leases: list[HandlerLease]) -> None:
        for lease in leases:
            self._registry.release(lease)

    def _is_tty(self, stream) -> bool:
        try:
            return (
                stream is not None
                and hasattr(stream, "isatty")
                and stream.isatty()
            )
        except Exception:
            return False

    def _file_handler_factory(self, **kwargs) -> logging.Handler | None:
        max_bytes = kwargs.get("max_bytes", 10 * 1024 * 1024)
        backup_count = kwargs.get("backup_count", 5)
        encoding = kwargs.get("encoding", "utf-8")
        file_handler = kwargs.get("file_handler")
        if file_handler is None:
            file_handler = FileStreamer(**kwargs)
        target = kwargs.get("target", file_handler.log_file_path)
        handler = logging.handlers.RotatingFileHandler(target, maxBytes=max_bytes, backupCount=backup_count, encoding=encoding, delay=True)
        handler.setLevel(kwargs.get("level", logging.INFO))
        handler.setFormatter(FileFormatter(**kwargs))
        return handler

    def acquire_file_handler(self, logger: logging.Logger, **kwargs) -> HandlerLease:
        kwargs["logger"] = logger
        kwargs["handler_type"] = logging.handlers.RotatingFileHandler
        kwargs["factory"] = self._file_handler_factory
        return self._registry.acquire(**kwargs)

    def _console_handler_factory(self, **kwargs) -> logging.Handler:
        handler = logging.StreamHandler(kwargs.get("stream", sys.stderr))
        handler.setLevel(kwargs.get("level", logging.INFO))
        handler.setFormatter(StreamFormatter(**kwargs))
        return handler

    def acquire_console_handler(self, logger: logging.Logger, stream = None, **kwargs) -> HandlerLease | None:
        stream = sys.stderr if stream is None else stream
        tty_required = kwargs.get("tty_required", False)
        if not self._is_tty(stream):
            if tty_required:
                raise ValueError("Failed to acquire console handler: stream is not a TTY")
            return
        kwargs["logger"] = logger
        kwargs["handler_type"] = logging.StreamHandler
        kwargs["target"] = f"console:{id(stream)}"
        kwargs["factory"] = self._console_handler_factory
        kwargs["stream"] = stream
        return self._registry.acquire(**kwargs)

    def _set_formatter_debug(self, handler: logging.Handler, flag: bool) -> None:
        formatter = getattr(handler, "formatter", None)
        if formatter is None:
            return
        setter = getattr(formatter, "_set_debug", None)
        if callable(setter):
            setter(flag)
        elif hasattr(formatter, "debug"):
            formatter.debug = flag

    def set_debug_for_leases(self, leases: list[HandlerLease], flag: bool) -> None:
        for lease in leases:
            self._set_formatter_debug(lease.handler, flag)
