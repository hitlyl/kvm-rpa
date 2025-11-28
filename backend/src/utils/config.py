"""配置管理模块

负责加载和管理系统配置，支持从 YAML 文件读取配置，并提供配置访问接口。
注意: YOLO、OCR、RTSP、KVM 等参数已迁移到流程节点属性中配置。
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    console: bool = Field(default=True, description="是否输出到控制台")
    file: bool = Field(default=True, description="是否输出到文件")
    file_path: str = Field(default="logs/rpa.log", description="日志文件路径")
    rotation: str = Field(default="10 MB", description="日志轮转周期")
    retention: str = Field(default="7 days", description="日志保留时间")


class MonitoringConfig(BaseModel):
    """监控配置"""
    enabled: bool = Field(default=False, description="是否启用监控")
    prometheus_port: int = Field(default=9090, description="Prometheus 指标端口")


class APIConfig(BaseModel):
    """API 服务配置"""
    host: str = Field(default="0.0.0.0", description="服务监听地址")
    port: int = Field(default=8000, description="服务监听端口")


class FlowsConfig(BaseModel):
    """流程配置"""
    directory: str = Field(default="flows", description="流程文件存储目录")
    auto_load: bool = Field(default=False, description="是否自动加载流程")
    auto_execute: bool = Field(default=False, description="是否自动执行流程")


class Config(BaseModel):
    """系统总配置
    
    注意: YOLO、OCR、RTSP、KVM 等参数已迁移到流程节点属性中配置。
    此配置仅包含系统级别的配置项。
    """
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    flows: FlowsConfig = Field(default_factory=FlowsConfig)


class ConfigManager:
    """配置管理器
    
    负责加载、解析和管理系统配置文件。支持从 YAML 文件加载配置，
    并提供配置访问接口。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 config/default.yaml
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config: Config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 从环境变量获取或使用默认路径
        env_path = os.getenv("KVM_RPA_CONFIG")
        if env_path:
            return env_path
        
        # 默认配置文件路径
        base_dir = Path(__file__).parent.parent.parent
        return str(base_dir / "config" / "default.yaml")
    
    def _load_config(self) -> Config:
        """加载配置文件
        
        Returns:
            Config: 配置对象
        """
        config_file = Path(self.config_path)
        
        # 如果配置文件不存在，使用默认配置
        if not config_file.exists():
            return Config()
        
        # 从 YAML 文件加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f) or {}
        
        # 解析为配置对象
        return Config(**config_dict)
    
    def reload(self) -> None:
        """重新加载配置文件"""
        self.config = self._load_config()
    
    def save(self, path: Optional[str] = None) -> None:
        """保存配置到文件
        
        Args:
            path: 保存路径，默认为当前配置文件路径
        """
        save_path = path or self.config_path
        config_dict = self.config.model_dump()
        
        # 确保目录存在
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 保存为 YAML 格式
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键，支持点号分隔的多级访问，如 "logging.level"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        
        return value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """更新配置项
        
        Args:
            updates: 更新的配置字典
        """
        config_dict = self.config.model_dump()
        
        # 递归更新字典
        def deep_update(base: dict, updates: dict) -> dict:
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    base[key] = deep_update(base[key], value)
                else:
                    base[key] = value
            return base
        
        config_dict = deep_update(config_dict, updates)
        self.config = Config(**config_dict)


# 全局配置实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_config() -> None:
    """重新加载全局配置"""
    global _config_manager
    if _config_manager is not None:
        _config_manager.reload()
