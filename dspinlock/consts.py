"""Module that contains the constants."""

import logging

SL_LOG_TAG = "D_SPINLOCK"
"""The logger name."""
SL_LOG_FORMAT = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
"""The logging format."""
SL_LOG_LEVEL = logging.INFO
"""The logging reporting level."""
SL_LOG_ENABLED: str = "SL_LOG_ENABLED"
"""Environment variable name that dictates if logging is enabled."""
