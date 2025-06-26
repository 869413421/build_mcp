import os
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from build_mcp.common.config import load_config
from build_mcp.common.logger import get_logger
from build_mcp.services.gd_sdk import GdSDK

# 优先从环境变量里读取API_KEY，如果没有则从配置文件读取
env_api_key = os.getenv("API_KEY")
config = load_config("config.yaml")
if env_api_key:
    config["api_key"] = env_api_key
mcp = FastMCP("amap-maps", description="高德地图 MCP 服务", version="1.0.0")
sdk = GdSDK(config=config, logger=get_logger(name="gd_sdk", log_file="gd_sdk.log", log_level=config.get("log_level", "INFO")))
logger = get_logger(name="amap-maps", log_file="amap_maps.log", log_level=config.get("log_level", "INFO"))


@mcp.tool(name="locate_ip", description="根据 IP 地址定位位置")
async def locate_ip(ip="") -> Dict[str, Any]:
    """
    根据 IP 地址定位位置。

    Args:
        ip (str): 要定位的 IP 地址。

    Returns:
        dict: 包含定位结果的字典。
    """
    logger.info(f"Locating IP: {ip}")
    try:
        result = await sdk.locate_ip(ip)
        if not result:
            return {"error": "get locate ip result is empty , please check your log."}
        logger.info(f"Locate IP result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error locating IP {ip}: {e}")
        return {"error": str(e)}


@mcp.tool(name="search_nearby", description="周边搜索")
async def search_nearby(location: str, keywords: str = "", types: str = "", radius: int = 1000, page_num: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
     周边搜索。

     Args:
         location (str): 中心点经纬度，格式为 "lng,lat"。
         keywords (str, optional): 搜索关键词，默认为空。
         types (str, optional): POI 分类，默认为空。
         radius (int, optional): 搜索半径（米），最大 50000，默认为 1000。
         page_num (int, optional): 页码，默认为 1。
         page_size (int, optional): 每页数量，最大 25，默认为 10。

     Returns:
         dict: 包含搜索结果的字典。
    """
    logger.info(f"Searching nearby: location={location}, keywords={keywords}, types={types}, radius={radius}, page_num={page_num}, page_size={page_size}")
    try:
        result = await sdk.search_nearby(location=location, keywords=keywords, types=types, radius=radius, page_num=page_num, page_size=page_size)
        if not result:
            return {"error": "search nearby result is empty , please check your log."}
        logger.info(f"Search nearby result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error searching nearby: {e}")
        return {"error": str(e)}
