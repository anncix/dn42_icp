#!/usr/bin/env python3
"""DN42 备案查询系统启动入口"""

import os
import sys
import argparse

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from config import Config

app = create_app()


def init_sync():
    """初始化同步"""
    from app.sync import RegistrySyncer
    from app.models import db
    from flask import current_app
    
    with app.app_context():
        print("开始同步 dn42 Registry 数据...")
        syncer = RegistrySyncer(
            Config.REGISTRY_REPO_URL,
            Config.REGISTRY_LOCAL_PATH
        )
        record = syncer.sync_to_database()
        print(f"同步完成：{record.message}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DN42 备案查询系统')
    parser.add_argument('--sync', action='store_true', help='同步数据后启动')
    parser.add_argument('--sync-only', action='store_true', help='仅同步数据，不启动服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='监听端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    if args.sync or args.sync_only:
        init_sync()
    
    if not args.sync_only:
        app.run(host=args.host, port=args.port, debug=args.debug)
