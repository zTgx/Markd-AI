#!/usr/bin/env python3
"""
Markd-AI: 构建和上传 Python 包到 PyPI 或 TestPyPI 的脚本
功能：
1. 构建源分发包和轮式分发包
2. 上传到 TestPyPI 或 PyPI
3. 支持环境变量配置 API 令牌
使用：
    python build_and_upload.py --repository testpypi
    python build_and_upload.py --repository pypi
依赖：
    pip install build twine
环境变量（可选）：
    TWINE_USERNAME: 通常为 __token__
    TWINE_PASSWORD: PyPI 或 TestPyPI 的 API 令牌
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

def run_command(command, error_message):
    """
    执行 shell 命令并处理错误
    :param command: 命令列表
    :param error_message: 错误提示信息
    """
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: {error_message}\n{e.stderr}")
        return False

def build_package():
    """
    构建 Python 包（sdist 和 wheel）
    :return: 成功返回 True，失败返回 False
    """
    print("正在构建包...")
    if not Path("pyproject.toml").exists():
        print("错误: 项目根目录缺少 pyproject.toml 文件")
        return False
    return run_command(
        [sys.executable, "-m", "build"],
        "构建失败，请检查 pyproject.toml 和依赖"
    )

def upload_package(repository):
    """
    上传包到指定的 PyPI 仓库
    :param repository: 'testpypi' 或 'pypi'
    :return: 成功返回 True，失败返回 False
    """
    print(f"正在上传到 {repository}...")
    dist_dir = Path("dist")
    if not dist_dir.exists() or not any(dist_dir.iterdir()):
        print("错误: dist 目录不存在或为空，请先构建包")
        return False
    
    command = [
        sys.executable, "-m", "twine", "upload",
        "--repository", repository,
        "dist/*"
    ]
    return run_command(
        command,
        f"上传到 {repository} 失败，请检查 API 令牌或网络连接"
    )

def main():
    """
    主函数，处理命令行参数并执行构建和上传
    """
    parser = argparse.ArgumentParser(
        description="构建和上传 Markd-AI 包到 PyPI 或 TestPyPI",
        epilog="示例: python build_and_upload.py --repository testpypi"
    )
    parser.add_argument(
        "--repository",
        choices=["testpypi", "pypi"],
        required=True,
        help="目标仓库：testpypi 或 pypi"
    )
    args = parser.parse_args()

    # 检查必要工具
    required_modules = ["build", "twine"]
    for module in required_modules:
        if not run_command(
            [sys.executable, "-m", "pip", "show", module],
            f"请安装 {module}: pip install {module}"
        ):
            sys.exit(1)

    # 检查环境变量中的 API 令牌
    if not os.getenv("TWINE_USERNAME") or not os.getenv("TWINE_PASSWORD"):
        print("警告: 未设置 TWINE_USERNAME 或 TWINE_PASSWORD 环境变量")
        print("请在命令行中输入 API 令牌，或在 ~/.pypirc 中配置")

    # 构建包
    if not build_package():
        sys.exit(1)

    # 上传包
    if not upload_package(args.repository):
        sys.exit(1)

    print(f"成功上传到 {args.repository}！")
    print(f"检查包: https://{'test.' if args.repository == 'testpypi' else ''}pypi.org/project/markdai/")

if __name__ == "__main__":
    main()