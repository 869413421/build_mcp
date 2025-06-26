# src/build_mcp/services/gd_sdk.py
import asyncio
import logging
from typing import Any

import httpx


class GdSDK:
    """
    GdSDK API 异步 SDK 封装。

    支持自动重试，指数退避策略。

    Args:
        config (dict): 配置字典，示例：
            {
                "base_url": "https://restapi.amap.com",
                "api_key": "your_api_key",
                "proxies": {"http": "...", "https": "..."},  # 可选
                "max_retries": 5,
                "retry_delay": 1,
                "backoff_factor": 2,
            }
        logger (logging.Logger, optional): 日志记录器，默认使用模块 logger。
    """

    def __init__(self, config: dict, logger=None):
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "").rstrip('/')
        self.proxy = config.get("proxy", None)
        self.logger = logger
        self.max_retries = config.get("max_retries", 5)
        self.retry_delay = config.get("retry_delay", 1)
        self.backoff_factor = config.get("backoff_factor", 2)

        # 创建一个异步HTTP客户端，自动带上请求头和代理配置
        self._client = httpx.AsyncClient(proxy=self.proxy, timeout=10)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._client.aclose()

    def _should_retry(self, response: httpx.Response = None, exception: Exception = None) -> bool:
        """
        判断请求失败后是否应该重试。

        Args:
            response (httpx.Response, optional): HTTP 响应对象。
            exception (Exception, optional): 请求异常。

        Returns:
            bool: 是否需要重试。
        """
        if exception is not None:
            # 网络异常等，建议重试
            return True

        if response is not None and response.status_code in (429, 500, 502, 503, 504):
            # 服务器错误或请求过多，建议重试
            return True

        # 其他情况不重试
        return False

    async def _request_with_retry(self, method: str, url: str, params=None, json=None):
        """
        发送HTTP请求，带自动重试和指数退避。

        Args:
            method (str): HTTP方法，如 'GET', 'POST'。
            url (str): 请求URL。
            params (dict, optional): URL查询参数。
            json (dict, optional): 请求体JSON。

        Returns:
            dict or None: 成功时返回JSON解析结果，失败返回 None。
        """
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"发送请求：{method} {url}，参数：{params}, JSON：{json}, 尝试次数：{attempt + 1}/{self.max_retries + 1}")
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                )
                self.logger.info(f"收到响应：{response.status_code} {response.text}")
                if response.status_code in [200, 201]:
                    # 成功返回JSON数据
                    return response.json()

                if not self._should_retry(response=response):
                    self.logger.error(f"请求失败且不可重试，状态码：{response.status_code}，URL：{url}")
                    return None

                self.logger.warning(
                    f"请求失败（状态码：{response.status_code}），"
                    f"第 {attempt + 1}/{self.max_retries} 次重试，URL：{url}"
                )

            except httpx.RequestError as e:
                self.logger.warning(
                    f"请求异常：{str(e)}，"
                    f"第 {attempt + 1}/{self.max_retries} 次重试，URL：{url}"
                )

            # 如果不是最后一次重试，按指数退避等待
            if attempt < self.max_retries:
                delay = self.retry_delay * (self.backoff_factor ** attempt)
                await asyncio.sleep(delay)

        self.logger.error(f"所有重试失败，URL：{url}")
        return None

    async def close(self):
        """
        关闭异步HTTP客户端，释放资源。
        """
        await self._client.aclose()

    async def locate_ip(self, ip: str = None) -> Any | None:
        """
        IP定位接口
        https://lbs.amap.com/api/webservice/guide/api/ipconfig

        Args:
            ip (str, optional): 要查询的 IP，若为空，则使用请求方公网 IP。

        Returns:
            dict: 定位结果，若失败则返回 None。
        """
        url = f"{self.base_url}/v3/ip"
        params = {
            "key": self.api_key,
        }
        if ip:
            params["ip"] = ip

        result = await self._request_with_retry(
            method="GET",
            url=url,
            params=params
        )

        if result and result.get("status") == "1":
            return result
        else:
            self.logger.error(f"IP定位失败: {result}")
            return None

    async def search_nearby(self, location: str, keywords: str = "", types: str = "", radius: int = 1000, page_num: int = 1, page_size: int = 20) -> dict | None:
        """
        周边搜索（新版 POI）
        https://lbs.amap.com/api/webservice/guide/api-advanced/newpoisearch#t4

        Args:
            location (str): 中心点经纬度，格式为 "lng,lat"
            keywords (str, optional): 搜索关键词
            types (str, optional): POI 分类
            radius (int, optional): 搜索半径（米），最大 50000，默认 1000
            page_num (int, optional): 页码，默认 1
            page_size (int, optional): 每页数量，默认 20，最大 25

        Returns:
            dict | None: 搜索结果，失败时返回 None
        """
        url = f"{self.base_url}/v5/place/around"
        params = {
            "key": self.api_key,
            "location": location,
            "keywords": keywords,
            "types": types,
            "radius": radius,
            "page_num": page_num,
            "page_size": page_size,
        }

        result = await self._request_with_retry(
            method="GET",
            url=url,
            params=params,
        )

        if result and result.get("status") == "1":
            return result
        else:
            self.logger.error(f"周边搜索失败: {result}")
            return None
