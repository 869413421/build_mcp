# tests/common/test_config.py
from build_mcp.common.config import load_config


def test_load_config():
    """测试配置文件加载功能"""
    config = load_config("config.yaml")
    assert config["api_key"] == "test"
    assert config["log_level"] == "INFO"
