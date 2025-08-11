from loguru import logger
import sys
from pathlib import Path

def setup_logger(debug: bool = False, log_file: str = "data/logs/almaa.log"):
    """Configure le système de logging"""

    # Remove default handler
    logger.remove()

    # Console logging
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )

    # File logging
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        rotation="500 MB",
        retention="7 days",
        level="DEBUG",
        format="{time} | {level} | {name}:{function}:{line} - {message}"
    )

    # Error logging
    logger.add(
        log_file.replace(".log", "_error.log"),
        rotation="100 MB",
        retention="30 days",
        level="ERROR",
        format="{time} | {level} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=True
    )

    return logger
