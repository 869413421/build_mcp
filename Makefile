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