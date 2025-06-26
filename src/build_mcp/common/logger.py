# src/build_mcp/common/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

from build_mcp.common.config import load_config

config = load_config("config.yaml")


def get_logger(name: str = "default", max_bytes=5 * 1024 * 1024, backup_count=3) -> logging.Logger:
    """
    获取一个带文件和控制台输出的 logger。

    Args:
        name (str): logger 名称，默认为 "default"。
        max_bytes (int): 单个日志文件最大大小，默认为 5MB。
        backup_count (int): 日志文件保留份数，默认为 3。
    Returns:
        logging.Logger: 配置好的 logger 实例。
    Example:
        logger = get_logger("my_logger")
        logger.info("This is an info message.")
    """
    log_level = config.get("log_level", "INFO")
    log_dir = config.get("log_dir", "./logs")
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{name}.log")

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False

    if not logger.hasHandlers():
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    logger.info(f"Logger 初始化完成，写入文件：{log_file}")
    return logger
