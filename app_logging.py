import logging


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level=logging.INFO):
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    else:
        root_logger.setLevel(level)

    return logging.getLogger(__name__)
