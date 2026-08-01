#!/usr/bin/env python3
"""
定期同步 dn42 Registry 数据的脚本
可通过 cron 定时执行

用法:
    python scripts/sync_registry.py
    
cron 示例 (每小时同步一次):
    0 * * * * cd /path/to/dn42_icp && python scripts/sync_registry.py >> logs/sync.log 2>&1
"""

import os
import sys
from datetime import datetime

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.sync import RegistrySyncer
from config import Config


def main():
    app = create_app()
    
    with app.app_context():
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{now}] 开始同步 dn42 Registry 数据...")
        
        syncer = RegistrySyncer(
            Config.REGISTRY_REPO_URL,
            Config.REGISTRY_LOCAL_PATH
        )
        
        try:
            record = syncer.sync_to_database()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] {record.message}")
            return 0 if record.status == 'success' else 1
        except Exception as e:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] 同步失败: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    sys.exit(main())
