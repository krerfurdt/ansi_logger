from ansi_logger import Logger

log = Logger(name="file_logger_test", log_dir="./", file_only=True)
log.info("This is an info message.")
log.warning("This is a warning message.")
log.error("This is an error message.")
log.critical("This is a critical message.")
log._set_debug(True)
log.debug("This is a debug message.")
log.info("This is a debug info message.")
log.warning("This is a debug warning message.")
log.error("This is a debug error message.")
log.critical("This is a debug critical message.")
