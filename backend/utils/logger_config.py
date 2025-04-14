from loguru import logger
import sys


def configure_logger():
    logger.remove()

    logger.add(
        sink=sys.stderr,
        level="DEBUG",
        format="<cyan>{time:YYYY-MM-DD HH:mm:ss}</cyan> | <blue>{name}</blue> | <green>{level}</green> | <magenta>{message}</magenta>",
    )

    return logger
