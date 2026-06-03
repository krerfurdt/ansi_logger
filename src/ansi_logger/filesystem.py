import os
import platform
import sys
import tempfile
import uuid
import inspect

APP_NAME = 'ANSI.logger'
DEFAULT_LINUX_LOG_DIR = os.path.join(os.environ.get('XDG_STATE_HOME', os.path.join(os.path.expanduser('~'), ".local", "state")), APP_NAME)
DEFAULT_WINDOWS_LOG_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), APP_NAME)
APP_LOCAL_LOG_DIR = os.path.join(os.getcwd(), "logs")

class FileStreamer:
    def __init__(self, **kwargs):
        self.current_os = platform.system()
        self.accepted_log_dirs = [DEFAULT_LINUX_LOG_DIR, DEFAULT_WINDOWS_LOG_DIR, APP_LOCAL_LOG_DIR]
        if 'log_dir' in kwargs and kwargs['log_dir']:
            self.log_dir_name = kwargs.get('log_dir')
        else:
            self.log_dir_name = self._get_default_log_dir()
        if 'log_file' in kwargs and kwargs['log_file']:
            self.log_file_name = kwargs.get('log_file')
        else:
            self.log_file_name = self._get_default_log_file_name() if kwargs.get('name') is None else kwargs.get('name')
        self.log_dir_name = self._sanitize_path(self.log_dir_name)
        self.log_file_name = self._sanitize_filename(self.log_file_name)
        self.log_file_path = os.path.join(self.log_dir_name, f"{self.log_file_name}.log")
        if self.current_os == "Windows":
            if len(self.log_file_path) > 260:
                raise ValueError(f"Combined log directory and file name length cannot exceed 260 characters on Windows: {self.log_dir_name} + {self.log_file_name}")
        os.makedirs(self.log_dir_name, exist_ok=True)
        try:
            with open(self.log_file_path, 'a', encoding=kwargs.get('encoding', 'utf-8')):
                pass
        except Exception as e:
            raise RuntimeError(f"Failed to create log file at {self.log_file_path}: {e}")
        
    def _sanitize_path(self, path: str) -> str:
        from pathlib import Path

        if path is None:
            raise ValueError("Log directory path cannot be None")
        path_text = str(path).strip()
        if not path_text:
            raise ValueError("Log directory path cannot be empty")
        if '\x00' in path_text:
            raise ValueError("Log directory path cannot contain null bytes")
        return str(Path(path_text).expanduser().resolve(strict=False))

    def _sanitize_filename(self, filename: str) -> str:
        import re
        import unicodedata
        from pathlib import PurePosixPath, PureWindowsPath

        SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
        if filename is None:
            raise ValueError("Log file name cannot be None")
        filename_text = unicodedata.normalize('NFKC', str(filename)).strip()
        if not filename_text:
            raise ValueError("Log file name cannot be empty")
        if '\x00' in filename_text:
            raise ValueError("Log file name cannot contain null bytes")
        if '/' in filename_text or '\\' in filename_text:
            raise ValueError(f"Log file name cannot contain path separators: {filename!r}")
        posix_path = PurePosixPath(filename_text)
        windows_path = PureWindowsPath(filename_text)
        if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
            raise ValueError(f"Log file name cannot be an absolute or drive qualified path: {filename!r}")
        if filename_text.lower().endswith('.log'):
            filename_text = filename_text[:-4]
        filename_text = SAFE_CHARS.sub('_', filename_text)
        filename_text = re.sub(r"_+", "_", filename_text)
        filename_text = filename_text.strip('._- ')
        if not filename_text or filename_text in {'.', '..', '/', '\\', '\\\\'}:
            raise ValueError(f"Invalid log file name: {filename!r}")
        if self.current_os == "Windows":
            filename_text = filename_text.strip(' .')
            reserved_base = filename_text.split(".", 1)[0].upper()
            if reserved_base in {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} or re.match(r"^(COM[1-9]|LPT[1-9])$", reserved_base):
                filename_text = f"_{filename_text}"
        elif self.current_os == "Linux":
            filename_text = filename_text.strip('.')
        return filename_text[:251]

    def _is_writable_folder(self, folder_path: str) -> bool:
        try:
            os.makedirs(folder_path, exist_ok=True)
            fd, test_path = tempfile.mkstemp(prefix='.write_test', dir=folder_path)
            try:
                with os.fdopen(fd, 'w') as f:
                    f.write('test')
            finally:
                try:
                    os.remove(test_path)
                except OSError:
                    pass
            return True
        except (Exception, OSError):
            return False

    def _get_default_log_dir(self) -> str:
        if self.current_os == "Windows":
            preferred = DEFAULT_WINDOWS_LOG_DIR
            fallback = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), APP_NAME)
        elif self.current_os == "Linux":
            preferred = DEFAULT_LINUX_LOG_DIR
            fallback = os.path.join(os.environ.get('XDG_STATE_HOME', os.path.join(os.path.expanduser('~'), ".local", "state")), APP_NAME)
        else:
            preferred = os.path.join(os.getcwd(), "logs")
            fallback = os.path.join(os.path.expanduser('~'), APP_NAME)
        if preferred and self._is_writable_folder(preferred):
            return preferred
        if fallback and self._is_writable_folder(fallback):
            return fallback
        cwd = os.path.join(os.getcwd(), "logs")
        if self._is_writable_folder(cwd):
            return cwd
        raise RuntimeError(f'No writable log directory found.')

    def _get_default_log_file_name(self) -> str:
        try:
            main_module_path = sys.argv[0] if len(sys.argv) > 0 else None
            if main_module_path:
                base_name = os.path.basename(main_module_path)
                return base_name
            frame = inspect.stack()[1]
            module = inspect.getmodule(frame[0])
            if module and hasattr(module, '__name__'):
                return module.__name__
            else:
                return f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        except Exception as e:
            raise RuntimeError(f"Failed to determine logger name: {e}")
