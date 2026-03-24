"""
统一的日志配置模块
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.config import LOGS_DIR, DEBUG


def setup_logger(name: str, log_file: str = None, level: int = None) -> logging.Logger:
    """
    创建统一格式的 Logger
    
    Args:
        name: Logger 名称
        log_file: 日志文件名（相对于 LOGS_DIR）
        level: 日志级别，默认根据 DEBUG 配置
    
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 设置日志级别
    if level is None:
        level = logging.DEBUG if DEBUG else logging.INFO
    logger.setLevel(level)
    
    # 创建日志目录
    if log_file:
        log_path = LOGS_DIR / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件 Handler（如果指定了日志文件）
    if log_file:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取已配置的 Logger（快捷方法）
    自动使用 name 作为日志文件名
    """
    return setup_logger(name, f"{name}.log")


# 默认应用 Logger
app_logger = setup_logger("AIOpsApp", "app.log")
