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
