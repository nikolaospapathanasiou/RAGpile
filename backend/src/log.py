from logging.config import dictConfig


def init_logger():

    config = {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",  # Only INFO and above
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARNING",  # Only WARNING and above
                "formatter": "standard",
                "stream": "ext://sys.stderr",
            },
        },
        "root": {"handlers": ["stdout", "stderr"], "level": "INFO"},
    }
    dictConfig(config)
