# 项目路径
src_dir := $(PWD)
# 虚拟环境路径
venv_dir := $(src_dir)/ai-chat-server
# Python解释器路径
python := $(venv_dir)/bin/python
# pip路径
pip := $(venv_dir)/bin/pip
# fastapi路径
fastapi := $(venv_dir)/bin/fastapi

# 默认目标
default: run

# 运行服务器
run:
	$(fastapi) dev $(src_dir)/main.py --port 8001

# 安装依赖
install:
	$(pip) install -r requirements.txt

# 创建requirements.txt文件
freeze:
	$(pip) freeze > requirements.txt

# 格式化代码
format:
	$(pip) install black
	$(venv_dir)/bin/black $(src_dir)

# 清理缓存文件
clean:
	rm -rf $(src_dir)/__pycache__
	rm -rf $(src_dir)/.pytest_cache
	rm -rf $(src_dir)/.coverage

# 检查代码
check:
	$(pip) install flake8
	$(venv_dir)/bin/flake8 $(src_dir)

# 帮助信息
help:
	@echo "Makefile commands for AI Chat Server:"
	@echo "  make run       - 运行FastAPI服务器（带热重载）"
	@echo "  make install   - 安装依赖包"
	@echo "  make freeze    - 生成requirements.txt文件"
	@echo "  make format    - 使用black格式化代码"
	@echo "  make clean     - 清理缓存文件"
	@echo "  make check     - 使用flake8检查代码风格"
	@echo "  make help      - 显示此帮助信息"

.PHONY: run install freeze format clean check help