# 工程化构建一个MCP服务，从开发调试到部署上线

MCP有多火，已经不需要我再赘述。作为一项新兴技术，中文互联网上对如何开发MCP服务的资料多如牛毛，但大多数语焉不详或者浅尝辄止，大多数案例都是照搬官方文档的示例简述一下水文。

作为一个开发者，我深知工程化的重要性。MCP服务的开发不仅仅是照猫画虎写两个服务接口那么简单，更需要考虑到代码结构、配置管理、日志记录、异常处理等方方面面。

经过探索和实践，我希望将一个MCP服务的开发流程整理成了一份详尽的指南，希望能帮助更多的开发者快速上手并构建出高质量的MCP服务。

---

## 构建一个什么样的MCP服务？

为了让我们有更好地实践目标，我们简单构建一个基于高德地图API的MCP 服务，具备以下核心功能：

### [根据用户ip获取用户的地理位置](https://lbs.amap.com/api/webservice/guide/api/ipconfig)

- 参数：`ip地址(可选，不传递默认获取当前主机IP)`
- 返回：用户的经纬度信息

### [根据用户的地理位置获取附近的POI信息](https://lbs.amap.com/api/webservice/guide/api-advanced/newpoisearch)

- 参数：`经度、纬度、POI类型`
- 返回：附近的POI信息列表

完成以上功能后，我们就可以通过大模型对话的获取真实的POI信息，举个例子。

- 用户：我想知道我附近的餐馆有哪些？
- MCP服务：根据您的位置，附近有以下餐馆：1. 餐馆A 2. 餐馆B 3. 餐馆C
- 用户：餐馆A的地址是什么？
- MCP服务：餐馆A的地址是：
    - 地址：XXX
    - 电话：XXX
    - 营业时间：XXX

#### 效果图
![效果图](https://github.com/869413421/build_mcp/blob/main/docs/images/1.png）

---

## 核心 MCP 概念

如果在开始之前你对MCP是什么完全没有概念，建议先阅读 [MCP 官方文档](https://modelcontextprotocol.io/introduction) 了解基本概念。

MCP 服务器可以提供三种主要类型的功能：

- Resources: 资源，客户端可以读取的类似文件的数据（如 API 响应或文件内容）

- Tools: 工具 ，LLM 可以调用的函数（经用户批准）

- Prompts: 提示 ，帮助用户完成特定任务的预先编写的模板

---

## 必备知识

在开始之前，建议您具备以下知识：

- Python 基础
- LLM（大语言模型）概念
- UV （Python 包管理工具）

---

## 系统要求

- Python 3.10 及以上版本
- Python MCP SDK 1.2.0

---

## 配置开发环境

**⚠ 请务必根据自己的操作系统调整命令，powershell 和 bash 的命令语法有所不同。**

作者使用的是windows+git终端。
本教程前半段与官方基本无异，可查考官方文档中[server开发示例](https://modelcontextprotocol.io/quickstart/server)。

### 安装UV

```shell
# Linux or macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```shell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 创建虚拟环境初始化项目

```shell
# 使用UV创建并进入项目目录
uv init build-mcp
cd build-mcp

# 创建虚拟环境
uv venv
source .venv/Scripts/activate

# 安装相关依赖
uv add mcp[cli] httpx pytest
```

---

## 规划项目目录结构（推荐 `src/` 布局）

```plaintext
build-mcp/
├── src/                         # 核心源码目录（Python包）
│   └── build_mcp/               # 主包命名空间
│       ├── __init__.py          # 包初始化文件
│       ├── __main__.py          # 命令行入口点
│       ├── common/              # 通用功能模块
│       │   ├── config.py        # 配置管理
│       │   └── logger.py        # 日志系统
│       └── services/            # 业务服务模块
│           ├── gd_sdk.py        # 高德服务集成
│           └── server.py        # 主服务实现
├── tests/                       # 测试套件目录
│   ├── common/                  # 通用模块测试
│   └── services/                # 服务模块测试
├── docs/                        # 项目文档
│   └── build‑mcp 项目开发指南.md # 核心文档
├── pyproject.toml               # 项目构建配置
├── Makefile                     # 自动化命令管理
└── README.md                    # 项目概览文档
```

### 结构设计解析

#### 核心设计：`src/` 布局（关键优势）

```plaintext
build-mcp/
└── src/
    └── mirakl_mcp/
        ├── ... 
```

**为什么采用这种结构？**

- ✅ **隔离安装环境**（核心价值）  
  测试时强制通过`pip install`安装包，避免直接引用源码路径，确保测试环境=用户运行环境
- ✅ **防止隐式路径依赖**  
  消除因开发目录在`sys.path`首位导致的错误导入（常见于无`src/`的传统布局）
- ✅ **打包安全性**  
  强制验证包内容是否被正确包含在分发文件中（缺失文件在测试中会立即暴露）
- ✅ **多环境一致性**  
  开发/测试/生产环境使用完全相同包结构，杜绝"在我机器上能跑"问题

> 📊 数据支持：PyPA官方调查显示，采用`src/`布局的项目打包错误率降低63%（[来源](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/))

---

## 编写工具代码

规划好目录后我们开始正式进行编码，一个正式规范的项目可能涉及到非常多的项目配置读取。首先第一步我们对配置文件读取功能进行封装。

### 使用`pyyaml`包来管理配置

```shell
uv add pyyaml
```

### 创建配置管理模块

```shell
mkdir -p src/build_mcp/common
touch src/build_mcp/__init__.py
touch src/build_mcp/common/__init__.py
touch src/build_mcp/common/config.py
```

### 创建配置文件

```shell
touch src/build_mcp/config.yaml
```

在 `src/build_mcp/config.yaml` 文件中添加以下内容：

```yaml
# 高德地图API配置
api_key: test
# 高德地图API的基础URL
base_url: https://restapi.amap.com
# 代理设置
proxy: http://127.0.0.1:10809
# 日志等级
log_level: INFO
# 接口重试次数
max_retries: 5
# 接口重试间隔时间（秒）
retry_delay: 1
# 指数退避因子
backoff_factor: 2
# 日志文件路径
log_dir: /var/log/build_mcp
```

⚠ `config.yaml` 文件需要放在 `src/build_mcp/` 目录下，这样在加载配置时可以正确找到。

这个配置文件仅仅作为一个工程化的示例，正式环境中不要将敏感信息（如API密钥）直接写入配置文件，建议使用环境变量或安全存储服务。

### 编写配置管理代码

```python
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

```

### 安装代码

⚠ 首次安装代码时需要使用 `pip install -e .` 命令，这样可以将当前目录作为一个可编辑的包安装到虚拟环境中。这样在开发过程中对代码的修改会立即生效，无需重新安装。

```shell
uv pip install -e .
```

### 编写测试代码

项目中尽可能详尽地编写测试代码是一个好习惯。在项目工程化中，我们尽可能为一些核心功能编写测试代码，以确保代码的正确性和稳定性。

```shell
mkdir -p tests/common
touch tests/common/test_config.py
```

```python
# tests/common/test_config.py
from build_mcp.common.config import load_config


def test_load_config():
    """测试配置文件加载功能"""
    config = load_config("config.yaml")
    assert config["api_key"] == "test"
    assert config["log_level"] == "INFO"

```

### 运行测试

```shell
uv run pytest tests
```

## 编写日志模块

作为一个程序员，是否能够快速定位问题，日志系统是非常重要的。
一个优秀的程序员，不仅要会写代码，还要会写日志。我们简单封装一个日志模块，方便后续使用。

```shell
touch src/build_mcp/common/logger.py
```

这里我们实现一个同时输出控制台和文件的日志系统，支持日志轮转和备份。

```python
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
```

目前为止，构建一个系统的基础模块已经构建完成。接下来我们将实现核心的服务功能。

## 编写高德地图请求SDK

根据[高德地图API文档](https://lbs.amap.com/api/webservice/guide/api/ipconfig)，我们需要实现两个主要功能：

1. 根据用户IP获取地理位置
2. 根据地理位置获取附近的POI信息

### 创建高德地图服务模块

```shell
mkdir -p src/build_mcp/services
touch src/build_mcp/services/__init__.py
touch src/build_mcp/services/gd_sdk.py
```

### 编写高德地图服务代码

```python
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
    self.logger = logger or logging.getLogger(__name__)
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
```

代码中实现了：

- 异步HTTP请求，支持自动重试和指数退避
- `locate_ip` 方法用于根据IP获取地理位置
- `search_nearby` 周边搜索方法，用于根据经纬度获取附近的POI信息

### 编写高德地图服务测试代码

```shell
mkdir -p tests/services
touch tests/services/test_gd_sdk.py
```

```python
# tests/test_gd_sdk_real.py
import logging
import os

import pytest
import pytest_asyncio

from build_mcp.services.gd_sdk import GdSDK

API_KEY = os.getenv("API_KEY", "your_api_key_here")  # 从环境变量获取 API Key，或使用默认值


@pytest_asyncio.fixture
async def sdk():
    config = {
        "base_url": "https://restapi.amap.com",
        "api_key": API_KEY,
        "max_retries": 2,
    }
    async with GdSDK(config, logger=logging.getLogger("GdSDK")) as client:
        yield client


@pytest.mark.asyncio
async def test_locate_ip(sdk):
    result = await sdk.locate_ip()
    assert result is not None, "locate_ip 返回 None"
    assert result.get("status") == "1", f"locate_ip 调用失败: {result}"
    assert "province" in result, "locate_ip 返回中不包含 province"


@pytest.mark.asyncio
async def test_search_nearby(sdk):
    result = await sdk.search_nearby(
        location="116.481488,39.990464",
        keywords="加油站",
        radius=3000,
        page_num=1,
        page_size=5
    )
    assert result is not None, "search_nearby 返回 None"
    assert result.get("status") == "1", f"search_nearby 调用失败: {result}"
    assert "pois" in result, "search_nearby 返回中不包含 pois"


```

### 运行测试

```shell
uv run pytest tests/services/test_gd_sdk.py
# 如果你有高德API Key，可以直接运行以下命令进行测试
API_KEY=你的key uv run pytest -s tests/services/test_gd_sdk.py
```

---

## 🚀 MCP 服务的三种传输协议简介

### 1. **`stdio`**

* **通信方式**：本地进程之间通过标准输入/输出（stdin/stdout）双向传输 JSON‑RPC 消息；
* **适用场景**：本地调用工具或子进程，如桌面应用中轻量级集成；
* **优点**：延迟低、实现简单、无需网络。

---

### 2. **`SSE`（Server‑Sent Events，服务器发送事件）**

* **通信方式**：基于 HTTP：客户端用 `POST` 发消息，服务器通过 `GET` 建立 `text/event‑stream` 单向推送；
* **当前状态**：属于已弃用（deprecated），从 MCP v2024‑11‑05 起被“streamable‑http”取代，但仍保留兼容性支持；
* **优点**：适合早期远程场景中仅需服务器推送的简易实现；
* **缺点**：仅服务器→客户端单向，连接不支持断点恢复。

---

### 3. **`streamable‑http`**

* **通信方式**：基于 HTTP 的双向传输：客户端通过 `POST` 请求 JSON‑RPC，服务器可以返回一次性响应（JSON）或流式 SSE 消息，另可通过 `GET` 建立服务器推送；
* **支持功能**：

    * 单一 `/mcp` 端点处理所有通信；
    * 会话管理（通过 `Mcp‑Session‑Id`）；
    * 流断点续传与消息重放（HTTP 断线恢复支持 `Last‑Event‑ID`）；
    * 向后兼容 SSE；
* **当前状态**：MCP v2025‑03‑26 起默认推荐使用，适用于云端和远程部署，是远程场景的首选；([modelcontextprotocol.io][1])

---

### 📊 协议对比概览

| 协议                  | 通信方向         | 使用场景    | 特性亮点              | 推荐程度   |
|---------------------|--------------|---------|-------------------|--------|
| **stdio**           | 双向（本地）       | 本地子进程调用 | 简单、低延迟、零网络依赖      | ⭐ 本地优选 |
| **SSE**             | 单向（服务器→客户端）  | 早期远程实现  | 实现简单，但不支持恢复       | ⚠️ 已弃用 |
| **streamable‑http** | 双向/可选 SSE 推送 | 云端/远程交互 | 单端点、多功能、断点续传、兼容性强 | ✅ 推荐使用 |

---

[1]: https://modelcontextprotocol.io/docs/concepts/transports?utm_source=chatgpt.com "Transports - Model Context Protocol"

## 编写 MCP 服务主程序

接下来我们编写 MCP 服务的主程序，处理客户端请求并调用高德地图 SDK。

```shell
touch src/build_mcp/services/server.py
```

```python
import os
from typing import Annotated
from typing import Any, Dict, Generic, Optional, TypeVar

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from pydantic import Field

from build_mcp.common.config import load_config
from build_mcp.common.logger import get_logger
from build_mcp.services.gd_sdk import GdSDK

# 优先从环境变量里读取API_KEY，如果没有则从配置文件读取
env_api_key = os.getenv("API_KEY")
config = load_config("config.yaml")
if env_api_key:
  config["api_key"] = env_api_key

# 初始化 FastMCP 服务
mcp = FastMCP("amap-maps", description="高德地图 MCP 服务", version="1.0.0")
sdk = GdSDK(config=config, logger=get_logger(name="gd_sdk"))
logger = get_logger(name="amap-maps")

# 定义通用的 API 响应模型
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
  success: bool
  data: Optional[T] = None
  error: Optional[str] = None
  meta: Optional[Dict[str, Any]] = None

  @classmethod
  def ok(cls, data: T, meta: Dict[str, Any] = None) -> "ApiResponse[T]":
    return cls(success=True, data=data, meta=meta)

  @classmethod
  def fail(cls, error: str, meta: Dict[str, Any] = None) -> "ApiResponse[None]":
    return cls(success=False, error=error, meta=meta)


# 定义 Prompt
@mcp.prompt(name="assistant", description="高德地图智能导航助手，支持IP定位、周边POI查询等")
def amap_assistant(query: str) -> str:
  return (
    "你是高德地图智能导航助手，精通 IP 定位 和 周边POI查询。请你根据用户的需求获取调取工具，获取用户需要的相关信息。\n"
    "## 调用工具的步骤：\n"
    "1. 调用 `locate_ip` 工具到获取用户的经纬度。\n"
    "2. 若成功获取经纬度，使用该经纬度调用 `search_nearby` 工具，结合搜索关键词进行周边信息的搜索。\n"
    "## 注意事项：\n"
    "- 不要主动要求用户提供经纬度信息，直接使用 `locate_ip` 工具获取。\n"
    "- 如果用户的需求中包含经纬度信息，可以直接使用该信息进行周边搜索。\n"
    f"用户的需求为：\n\n {query}。\n"
  )


@mcp.tool(name="locate_ip", description="获取用户的 IP 地址定位信息，返回省市区经纬度等信息。")
async def locate_ip(ip: Annotated[Optional[str], Field(description="用户的ip地址")] = None) -> ApiResponse:
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
      ApiResponse.fail("定位结果为空，请检查日志，系统异常请检查相关日志，日志默认路径为/var/log/build_mcp。")
    logger.info(f"Locate IP result: {result}")
    return ApiResponse.ok(data=result, meta={"ip": ip})
  except Exception as e:
    logger.error(f"Error locating IP {ip}: {e}")
    return ApiResponse.fail(str(e))


@mcp.tool(name="search_nearby", description="根据经纬度和关键词进行周边搜索，返回指定半径内的 POI 列表。")
async def search_nearby(
        location: Annotated[str, Field(description="中心点经纬度，格式为 'lng,lat'，如 '116.397128,39.916527'")],
        keywords: Annotated[str, Field(description="搜索关键词，例如: '餐厅'。", min_length=0)] = "",
        types: Annotated[str, Field(description="POI 分类码，多个分类用逗号分隔")] = "",
        radius: Annotated[int, Field(description="搜索半径（米），最大50000", ge=0, le=50000)] = 1000,
        page_num: Annotated[int, Field(description="页码，从1开始", ge=1)] = 1,
        page_size: Annotated[int, Field(description="每页数量，最大25", ge=1, le=25)] = 20,
) -> ApiResponse:
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
      return ApiResponse.fail("搜索结果为空，请检查日志，系统异常请检查相关日志，日志默认路径为/var/log/build_mcp。")
    logger.info(f"Search nearby result: {result}")
    return ApiResponse.ok(data=result, meta={
      "location": location,
      "keywords": keywords,
      "types": types,
      "radius": radius,
      "page_num": page_num,
      "page_size": page_size
    })
  except Exception as e:
    logger.error(f"Error searching nearby: {e}")
    return ApiResponse.fail(str(e))
```

代码中我们封装了统一的响应类，提供了两个工具函数：
- `locate_ip`：根据 IP 地址获取地理位置
- `search_nearby`：根据经纬度和关键词进行周边搜索

**需要注意的是代码中Annotated类型是必不可少的，这样能让LLM通过元信息更加精准地调用工具。
目前看到大部分开发者开发的MCP服务都没有这种意识，只是单纯地定义工具，其实效果非常糟糕的。**

**同时我们编写了一个prompt，这个prompt会提供在对话上下文中，是非常重要的一点，也是很多开发者并没有意识到的。
AI时代，我们不仅要写得好代码，更要学会如何对提示词进行打磨**

其实文章主要核心在以上这部分代码，请认真去理解这部分信息。

至此，我们已经完成了 MCP 服务的核心功能实现。接下来，我们需要编写服务入口，启动 MCP 服务。

### 编写 MCP 服务入口

```shell
touch src/build_mcp/__init__.py
```

```python
# src/build_mcp/__init__.py
import argparse
import asyncio

from build_mcp.common.logger import get_logger
from build_mcp.services.server import mcp


def main():
    """Main function to run the MCP server."""
    logger = get_logger('app')

    parser = argparse.ArgumentParser(description="Amap MCP Server")
    parser.add_argument(
        'transport',
        nargs='?',
        default='stdio',
        choices=['stdio', 'sse', 'streamable-http'],
        help='Transport type (stdio, sse, or streamable-http)'
    )
    args = parser.parse_args()

    logger.info(f"🚀 Starting MCP server with transport type: %s", args.transport)

    try:
        mcp.run(transport=args.transport)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("🛑 MCP Server received shutdown signal. Cleaning up...")
    except Exception as e:
        logger.exception("❌ MCP Server crashed with unhandled exception: %s", e)
    else:
        logger.info("✅ MCP Server shut down cleanly.")


if __name__ == "__main__":
    main()

```

```shell
touch src/build_mcp/__main__.py
```

```python
# src/build_mcp/__main__.py
from build_mcp import main

if __name__ == "__main__":
    main()
```

### 修改`pyproject.toml` 文件

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "build-mcp"
version = "0.1.0"
description = "构建 MCP 服务器"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "httpx>=0.28.1",
  "mcp[cli]>=1.9.4",
  "pytest>=8.4.1",
  "pytest-asyncio>=1.0.0",
  "pyyaml>=6.0.2",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[project.scripts]
build_mcp = "build_mcp.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["src/build_mcp"]
```

其中重点为

```
[project.scripts]
build_mcp = "build_mcp.__main__:main"
```

这表示：
> 执行 build_mcp 命令时，会等价于运行：

```python
from build_mcp import main
main()
```

我们可以通过以下命令来运行 MCP 服务：

- 启动stdio协议的MCP服务：
```shell
uv run build_mcp
```

- 启动streamable-http协议的MCP服务：
```shell
uv run build_mcp streamable-http
```


## 调试MCP服务

如何调试MCP服务取决与我们启动服务的方式。

### 1.编写客户端代码进行调试stdio协议的MCP服务

```shell
mkdir -p tests/services
touch tests/services/test_mcp_client.py
```

```python
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.asyncio
async def test_mcp_server():
    async with stdio_client(
            StdioServerParameters(command="uv", args=["run", "build_mcp"])
    ) as (read, write):
        print("启动服务端...")

        async with ClientSession(read, write) as session:
            await session.initialize()
            print("初始化完成")

            tools = await session.list_tools()
            print("可用工具：", tools)

            assert hasattr(tools, "tools")
            assert isinstance(tools.tools, list)
            assert any(tool.name == "locate_ip" for tool in tools.tools)
```

#### 运行测试

```shell
API_KEY=你的API_KEY uv run pytest -s tests/services/test_mcp_client.py 
```

这是一个测试代码的，这里仅仅是一个示例，你可以根据自己的需求编写更多的测试代码来验证MCP服务的功能。

### 2.使用Inspector进行测试
Inspector是官方提供的一个MCP服务调试工具，可以通过它来启动一个本地web界面，在界面中可以直接调用MCP服务的工具。
相对更加直观和易用，比较推荐这种方式，详情可以查看[官方文档](https://modelcontextprotocol.io/docs/tools/inspector)。

```shell
# 使用Inspector调试stdio协议的MCP服务
API_KEY=你的KEY mcp dev src/build_mcp/__init__.py
```

## 编写Makefile
为了方便开发和测试，我们可以编写一个Makefile来管理常用的命令。

```shell
touch Makefile
```

```makefile
# Makefile for MCP Service

# 默认目标 - 显示帮助信息
.DEFAULT_GOAL := help

# 项目环境变量
API_KEY ?= your_api_key_here  # 默认测试用的 API_KEY

# 安装项目依赖
install:
	@echo "Installing project dependencies..."
	uv pip install -e .

# 运行测试 (需要设置 API_KEY)
test:
	@echo "Running tests with API_KEY=$(API_KEY)..."
	API_KEY=$(API_KEY) uv run pytest -s tests

# 启动 stdio 协议的 MCP 服务
stdio:
	@echo "Starting MCP service with stdio protocol..."
	uv run build_mcp

# 启动 streamable-http 协议的 MCP 服务
http:
	@echo "Starting MCP service with streamable-http protocol..."
	uv run build_mcp streamable-http

# dev
dev:
	@echo "Starting MCP service with stdio protocol in development mode..."
	API_KEY=$(API_KEY) mcp dev src/build_mcp/__init__.py

# 别名目标
streamable-http: http

# 帮助信息
help:
	@echo "MCP Service Management"
	@echo ""
	@echo "Usage:"
	@echo "  make install        Install project dependencies"
	@echo "  make test           Run tests (set API_KEY in Makefile or override)"
	@echo "  make stdio          Start MCP service with stdio protocol"
	@echo "  make http           Start MCP service with streamable-http protocol"
	@echo ""
	@echo "Advanced:"
	@echo "  Override API_KEY:   make test API_KEY=custom_key"
	@echo "  Clean:              make clean"
	@echo "  Full setup:         make setup"

# 清理项目
clean:
	@echo "Cleaning project..."
	rm -rf build dist *.egg-info
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

# 完整设置：清理 + 安装 + 测试
setup: clean install test
	@echo "Project setup completed!"

# 声明伪目标
.PHONY: install test stdio http streamable-http help clean setup
```

目前为止我们已经从0到1完整开发完了一整个MCP服务，恭喜自己又学会了一个新技能！

## 如何使用这个MCP服务？
首先你得拥有一个MCP客户端，目前市场上各种类型得MCP客户端层出不穷，至于用什么全凭你的爱好了。

这里有一份非常详细的MCP客户端使用攻略，是github上一个非常棒的项目：[MCP客户端使用攻略](https://github.com/yzfly/Awesome-MCP-ZH)

选择一个客户端下载安装，然后我们对我们开发的服务进行配置。

### 配置Stdio协议的MCP服务

```shell
{
    "mcpServers": {
        "build_mcp": {
            "command": "uv",
            "args": [
                "run",
                "-m"
                "build_mcp"
            ],
            "env": {
                "API_KEY": "你的高德API Key"
            }
        }
    }
}
```
⚠ 要注意本地UV环境，如果安装了多个UV可能会导致环境混乱，这是开发过程中比较头疼的一点，要自己注意。

### 配置Streamable-HTTP协议的MCP服务

#### 启动项目
```shell
make streamable-http
```

```shell
$ make streamable-http
Starting MCP service with streamable-http protocol...
uv run build_mcp streamable-http
[2025-06-26 15:01:33,775] INFO - Logger 初始化完成，写入文件：/var/log/build_mcp\gd_sdk.log
[2025-06-26 15:01:33,839] INFO - Logger 初始化完成，写入文件：/var/log/build_mcp\amap-maps.log
[2025-06-26 15:01:33,847] INFO - Logger 初始化完成，写入文件：/var/log/build_mcp\app.log
[2025-06-26 15:01:33,848] INFO - 🚀 Starting MCP server with transport type: streamable-http
INFO:     Started server process [6064]
INFO:     Waiting for application startup.
[06/26/25 15:01:33] INFO     StreamableHTTP session manager started                                                                                                                                     streamable_http_manager.py:109
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

```
启动成功后会在8000端口启动一个HTTP服务。


#### 客户端配置
```shell
{
    "mcpServers": {
        "build_mcp_http": {
            "url": "http://localhost:8000/mcp"
        }
    }
}
```

## 总结
本文介绍了如何从零开始构建一个高德地图的MCP服务，涵盖了以下内容：
- MCP服务的基本概念和配置
- 如何使用高德地图API进行IP定位和周边搜索
- 如何编写MCP服务的核心功能，包括配置管理、日志系统和高德地图SDK
- 如何编写MCP服务的主程序和入口
- 如何调试MCP服务，包括使用Inspector和编写测试代码
- 如何使用Makefile管理项目命令
- 如何配置MCP客户端连接到我们的服务

行文至此结束，祝大家学习愉快！如果你有任何问题或建议，请提交issue或pull request到[GitHub仓库](https://github.com/869413421/build_mcp)


## 参考资料
- [Model Context Protocol (MCP) 官方文档](https://modelcontextprotocol.io/docs/)
- [高德地图API文档](https://lbs.amap.com/api/webservice/guide/api/ipconfig)
- [官方开发SDK](https://github.com/modelcontextprotocol/python-sdk/tree/main)
  




