# src/build_mcp/common/logger.py
import logging
from logging.handlers import RotatingFileHandler


def get_logger(
        name: str = "default",
        log_file: str = "app.log",
        log_level=logging.INFO,
        max_bytes=5 * 1024 * 1024,
        backup_count=3
) -> logging.Logger:
    """
    获取一个带文件和控制台输出的 logger。

    Args:
        name (str): logger 名称
        log_file (str): 日志文件路径
        log_level (int): 日志等级，默认为 logging.INFO
        max_bytes (int): 单个日志文件最大大小（默认 5MB）
        backup_count (int): 日志文件保留份数
    Returns:
        logging.Logger: 配置好的 logger 实例
    Example:
        logger = get_logger("my_logger", "my_app.log", logging.DEBUG)
        logger.info("This is an info message.")
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.hasHandlers():  # 避免重复添加 handler
        # 控制台输出
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        # 文件输出
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
