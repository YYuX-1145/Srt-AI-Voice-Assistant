import logging

log_colors = {
    "DEBUG": "white",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}
logger = logging.getLogger()
logger.setLevel(logging.INFO)
try:
    import colorlog

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            fmt="%(log_color)s[%(levelname)s][%(asctime)s]:%(funcName)s: %(message)s",
            datefmt="%Y-%m-%d_%H:%M:%S",
            log_colors=log_colors,
        )
    )
    logger.addHandler(handler)
except ImportError:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(levelname)s][%(asctime)s]:%(funcName)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("彩色提示信息不可用，可选择安装依赖：colorlog")

from .settings import load_cfg
config=load_cfg()
