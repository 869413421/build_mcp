import logging
import os

import pytest
import pytest_asyncio

from build_mcp.services.gd_sdk import GdSDK
from build_mcp.common.logger import get_logger

API_KEY = os.getenv("API_KEY", "your_api_key_here")  # 从环境变量获取 API Key，或使用默认值


@pytest_asyncio.fixture
async def sdk():
    config = {
        "base_url": "https://restapi.amap.com",
        "api_key": API_KEY,
        "max_retries": 2,
    }
    async with GdSDK(config, logger=get_logger("gd_sdk_test")) as client:
        yield client


@pytest.mark.asyncio
async def test_locate_ip(sdk):
    result = await sdk.locate_ip()
    print(result)
    assert result is not None, "locate_ip 返回 None"
    assert result.get("status") == "1", f"locate_ip 调用失败: {result}"
    assert "province" in result, "locate_ip 返回中不包含 province"


@pytest.mark.asyncio
async def test_search_nearby(sdk):
    result = await sdk.search_nearby(
        location="113.1017375,22.93212254",
        keywords="加油站",
        radius=3000,
        page_num=1,
        page_size=1
    )
    print(result)
    assert result is not None, "search_nearby 返回 None"
    assert result.get("status") == "1", f"search_nearby 调用失败: {result}"
    assert "pois" in result, "search_nearby 返回中不包含 pois"
