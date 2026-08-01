import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dn42-beian-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(BASE_DIR, 'data', 'dn42_beian.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # dn42 Registry 配置
    REGISTRY_REPO_URL = 'https://git.dn42.dev/dn42/registry.git'
    REGISTRY_LOCAL_PATH = os.path.join(BASE_DIR, 'data', 'registry')
    REGISTRY_SYNC_INTERVAL = 3600  # 同步间隔（秒）
    
    # 站点配置
    SITE_NAME = 'DN42 备案查询系统'
    SITE_DESC = 'dn42 网络资源备案信息查询平台'
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # 分页配置
    PER_PAGE = 20
