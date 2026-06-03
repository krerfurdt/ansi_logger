import copy as copy
import logging
import unicodedata
from .ansi import AnsiFormatter

DEFAULT_FORMAT_STRING = '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s'

class StreamFormatter(logging.Formatter):
    def __init__(self, **kwargs):
        super().__init__(DEFAULT_FORMAT_STRING)
        self.debug = kwargs.get('debug', False)
        self.ansi_formatter = AnsiFormatter()

    def _color_by_level(self, text: str, record: logging.LogRecord) -> str:
        if record.exc_info:
            return self.ansi_formatter.format_text(text, fg_color='FG_GREEN', styles=['BOLD'], debug = self.debug)
        elif record.levelno == logging.DEBUG:
            return self.ansi_formatter.format_text(text, fg_color='FG_CYAN', debug = self.debug)
        elif record.levelno == logging.INFO:
            return self.ansi_formatter.format_text(text, fg_color='FG_WHITE', debug = self.debug)
        elif record.levelno == logging.WARNING:
            return self.ansi_formatter.format_text(text, fg_color='FG_BLUE', debug = self.debug)
        elif record.levelno == logging.ERROR:
            return self.ansi_formatter.format_text(text, fg_color='FG_YELLOW', debug = self.debug)
        elif record.levelno == logging.CRITICAL:
            return self.ansi_formatter.format_text(text, fg_color='FG_RED', styles=['BOLD'], debug = self.debug)
        else:
            return self.ansi_formatter.format_text(text, reset = 'ALL', debug = self.debug)

    def _set_format_string(self, format_string: str):
        self._style._fmt = format_string

    def formatException(self, exc_info) -> str:
        traceback_text = super().formatException(exc_info)
        if not traceback_text:
            return traceback_text
        colored_lines = []
        lines = traceback_text.splitlines()
        for index, line in enumerate(lines):
            stripped = line.lstrip()
            if index == 0 and line.startswith("Traceback"):
                colored_lines.append(self.ansi_formatter.format_text(line, fg_color="FG_MAGENTA", styles=["BOLD"], debug=False))
            elif stripped.startswith("File "):
                colored_lines.append(self.ansi_formatter.format_text(line, fg_color="FG_CYAN", debug=False))
            elif index == len(lines) - 1:
                colored_lines.append(self.ansi_formatter.format_text(line, fg_color="FG_RED", styles=["BOLD"], debug=False))
            else:
                colored_lines.append(self.ansi_formatter.format_text(line, fg_color="FG_WHITE", styles=["DIM"], debug=False))
        return "\n".join(colored_lines)

    def format(self, record: logging.LogRecord) -> str:
        original_record = copy.copy(record)
        try:
            msg = original_record.getMessage()
            if isinstance(msg, str):
                msg = unicodedata.normalize('NFC', msg)
                msg = msg.replace('\n', ' ↵ ').replace('\r', '')
                msg = self._color_by_level(msg, original_record)
            original_record.msg = msg
            original_record.args = ()
            if original_record.exc_info and original_record.exc_info[0] is None:
                original_record.exc_info = None
            original_record.exc_text = None
            return super().format(original_record)
        except Exception as e:
            raise RuntimeError(f"Failed to color format log record: {e}")

class FileFormatter(logging.Formatter):
    def __init__(self, **kwargs):
        super().__init__(DEFAULT_FORMAT_STRING)
        self.debug = kwargs.get('debug', False)
        self.ensure_ascii = kwargs.get('ensure_ascii', False)

    def format(self, record: logging.LogRecord) -> str:
        original_record = copy.copy(record)
        try:
            msg = original_record.getMessage()
            if isinstance(msg, str):
              msg = unicodedata.normalize('NFC', msg)
              msg = msg.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
              msg = msg.encode('ascii', 'backslashreplace').decode('ascii') if self.ensure_ascii else msg
            original_record.msg = msg
            original_record.args = ()
            if original_record.exc_info and original_record.exc_info[0] is None:
                original_record.exc_info = None
            original_record.exc_text = None
            return super().format(original_record)
        except Exception as e:
            raise RuntimeError(f"Failed to file format log record: {e}")
