"""
Description: Configuration for logging
"""

from pythonjsonlogger.jsonlogger import JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    def __init__(self, *args, **kwargs):
        kwargs.update({"rename_fields": {"asctime": "timestamp", "levelname": "severity"}})
        super().__init__(*args, **kwargs)


def get_config(log_level="WARNING", log_formatter="verbose", log_http=False):
    """
    Docs: https://docs.djangoproject.com/en/4.0/howto/logging/
    """

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': "[%(asctime)s] %(levelname)s [%(name)s: %(funcName)s: %(lineno)s] %(message)s",
                'datefmt': "%Y-%m-%dT%H:%M:%S%z"
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
            'json': {
                "()": "baazaar.logging_config.CustomJsonFormatter",
                "fmt": "%(levelname)s %(asctime)s %(name)s %(funcName)s %(lineno)s %(message)s"
            },
            'http': {
                'format': "[%(asctime)s] %(levelname)s [http:log] %(message)s",
                "()": "baazaar.utils.logger.RequestResponseFormatter",
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': log_formatter
            },
            'json': {
                'formatter': 'json',
                'class': 'logging.StreamHandler',
            },
            'http': {
                'formatter': 'http',
                'class': 'logging.StreamHandler',
            }
        },
        'loggers': {
            # custom logger
            '_http': {
                'handlers': ['http'] if log_http else [],
                'level': log_level,
                'propagate': False,
            },
            'django': {
                'handlers': ['console'],
                'level': log_level,
                'propagate': False,
            },
            '': {
                'handlers': ['console'],
                'level': log_level,
                'propagate': False,
            },
        },
    }
