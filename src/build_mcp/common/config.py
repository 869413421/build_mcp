# src/build_mcp/common/config.py
import os

import yaml


def load_config(config_file="config.yaml") -> dict:
    """
    加载配置文件。

    Args:
        config_file (str): 配置文件的名称，默认为 "config.yaml"。
    Returns:
        dict: 返回配置文件的内容。
    Example:
        config = load_config("config.yaml")
        print(config)
    """
    # 找到根目录（config.yaml 就放根目录）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, config_file)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config
