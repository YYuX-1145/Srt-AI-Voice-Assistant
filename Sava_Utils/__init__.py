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

import argparse
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-p", "--server_port",type=int,help="server_port")
parser.add_argument('-share', dest='share', action="store_true", default=False, help="set share True")
parser.add_argument('-server_mode', dest='server_mode', action="store_true", default=False, help="activate server mode")
args, unknown = parser.parse_known_args()

from .settings import load_cfg
from .utils import cls_cache
config=load_cfg()
config.server_mode=args.server_mode or config.server_mode
if config.server_mode:
    logger.warning("服务模式已启用！")
if config.clear_tmp:
    cls_cache()