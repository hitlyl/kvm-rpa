"""日志模块

基于 loguru 提供统一的日志配置和管理功能。
"""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger


class LoggerManager:
    """日志管理器
    
    负责配置和管理系统日志，支持控制台和文件输出，以及日志轮转。
    """
    
    _initialized = False
    
    @classmethod
    def setup(
        cls,
        level: str = "INFO",
        console: bool = True,
        file_enabled: bool = True,
        file_path: str = "logs/kvm_rpa.log",
        rotation: str = "1 day",
        retention: str = "90 days",
        format_string: Optional[str] = None
    ) -> None:
        """配置日志系统
        
        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console: 是否输出到控制台
            file_enabled: 是否输出到文件
            file_path: 日志文件路径
            rotation: 日志轮转周期 (如 "1 day", "100 MB")
            retention: 日志保留时间 (如 "90 days")
            format_string: 自定义日志格式
        """
        if cls._initialized:
            logger.warning("日志系统已初始化，跳过重复配置")
            return
        
        # 移除默认的 handler
        logger.remove()
        
        # 默认日志格式
        if format_string is None:
            format_string = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
        
        # 控制台输出
        if console:
            logger.add(
                sys.stdout,
                format=format_string,
                level=level,
                colorize=True,
                backtrace=True,
                diagnose=True
            )
        
        # 文件输出
        if file_enabled:
            # 确保日志目录存在
            log_file = Path(file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                file_path,
                format=format_string,
                level=level,
                rotation=rotation,
                retention=retention,
                compression="zip",  # 压缩旧日志
                backtrace=True,
                diagnose=True,
                encoding="utf-8"
            )
        
        cls._initialized = True
        logger.info(f"日志系统已初始化 - 级别: {level}, 控制台: {console}, 文件: {file_enabled}")
    
    @classmethod
    def get_logger(cls):
        """获取日志对象
        
        Returns:
            logger: loguru logger 对象
        """
        if not cls._initialized:
            logger.warning("日志系统未初始化，使用默认配置")
            cls.setup()
        return logger


def setup_logger(
    level: str = "INFO",
    console: bool = True,
    file_enabled: bool = True,
    file_path: str = "logs/kvm_rpa.log",
    rotation: str = "1 day",
    retention: str = "90 days"
) -> None:
    """配置日志系统（便捷函数）
    
    Args:
        level: 日志级别
        console: 是否输出到控制台
        file_enabled: 是否输出到文件
        file_path: 日志文件路径
        rotation: 日志轮转周期
        retention: 日志保留时间
    """
    LoggerManager.setup(
        level=level,
        console=console,
        file_enabled=file_enabled,
        file_path=file_path,
        rotation=rotation,
        retention=retention
    )


def get_logger():
    """获取日志对象（便捷函数）
    
    Returns:
        logger: loguru logger 对象
    """
    return LoggerManager.get_logger()

