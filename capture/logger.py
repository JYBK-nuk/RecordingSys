# logger.py

from loguru import logger
import sys

# 移除任何預設的處理器
logger.remove()

# 配置日誌器，包含模組名稱作為前綴
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | "
    "<level>{level}</level> | "
    "<cyan>{module}</cyan> | "
    "<level>{message}</level>",
)

# 設置日誌級別和顏色
logger.level("INFO", color="<white>")
logger.level("DEBUG", color="<cyan>")
logger.level("WARNING", color="<yellow>")
logger.level("ERROR", color="<red>")

# 導出 logger，供其他模組使用
__all__ = ["logger"]
