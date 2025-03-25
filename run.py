#!/usr/bin/env python
"""个人知识库系统启动脚本"""

import os
import sys
import argparse
import subprocess
from config import APP_CONFIG


def main():
    """主函数，解析命令行参数并启动应用"""
    parser = argparse.ArgumentParser(description="个人知识库系统启动脚本")
    parser.add_argument(
        "--port", 
        type=int, 
        default=APP_CONFIG["port"],
        help=f"应用端口号，默认为{APP_CONFIG['port']}"
    )
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="重置知识库（清空所有文档和向量存储）"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="启用调试模式"
    )
    
    args = parser.parse_args()
    
    # 构建Streamlit命令
    cmd = [
        "streamlit", 
        "run", 
        "app.py",
        "--server.port", str(args.port),
        "--browser.serverAddress", "localhost",
        "--server.headless", "true",  # 无头模式，不自动打开浏览器
    ]
    
    # 添加调试参数
    if args.debug:
        cmd.extend(["--logger.level", "debug"])
    else:
        cmd.extend(["--logger.level", "warning"])
    
    # 添加重置参数
    if args.reset:
        os.environ["RESET_KNOWLEDGE_BASE"] = "1"
    
    # 打印启动信息
    print(f"正在启动个人知识库系统，端口: {args.port}")
    print(f"启动后请访问: http://localhost:{args.port}")
    
    # 启动应用
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()