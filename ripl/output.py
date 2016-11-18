import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("ripl-main")


def raw_info(message):
    logger.info(message)

def info(stage, message):
    logger.info("[{0}] {1}".format(stage, message))

def warning(stage, message):
    logger.warning("[{0}] Warning: {1}".format(stage, message))

def error(stage, message):
    logger.error("[{0}] Error: {1}".format(stage, message))
