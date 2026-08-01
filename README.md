# DN42 备案查询系统

一套类似萌备案风格的 dn42 网络资源备案查询系统，基于 dn42 Registry 数据构建。

## 功能特性

### 前台功能
- 🔍 **全站搜索** - 支持 AS号、域名、IP段、维护者等多维度关键词搜索
- 📋 **分类浏览** - 按对象类型浏览（aut-num、inetnum、inet6num、dns、mntner、person 等）
- 📄 **详情展示** - 完整展示 RPSL 格式数据，支持关联对象跳转
- 📊 **数据统计** - 各类型对象数量统计、同步历史记录
- 🔥 **热门排行** - 按访问量展示热门备案记录
- 🕐 **最近更新** - 展示最新更新的备案信息
- 🌙 **深色主题** - 现代化暗色界面设计

### 后台功能
- 🔐 **管理员登录** - 基于 Flask-Login 的权限控制
- 🔄 **一键同步** - 手动触发 dn42 Registry 数据同步
- 📋 **对象管理** - 浏览和查看所有备案对象
- 📈 **数据概览** - 后台仪表盘展示统计信息

### API 接口
- `GET /api/search?q=关键词&type=类型&page=页码` - 搜索接口
- `GET /api/detail/<类型>/<主键>` - 详情接口
- `GET /api/stats` - 统计数据接口

## 技术栈

- **后端**: Python 3.8+ / Flask / SQLAlchemy
- **数据库**: SQLite（默认，可切换 PostgreSQL/MySQL）
- **前端**: 原生 HTML + CSS + JavaScript（无框架依赖）
- **数据源**: dn42 Registry Git 仓库
- **认证**: Flask-Login + Werkzeug 密码哈希

## 快速开始

### 1. 安装依赖

```bash
cd dn42_icp
pip install -r requirements.txt
```

### 2. 首次同步数据

```bash
# 方式一：同步数据并启动服务
python run.py --sync

# 方式二：仅同步数据
python run.py --sync-only
```

### 3. 启动服务

```bash
python run.py
# 默认监听 0.0.0.0:5000
```

访问 http://localhost:5000 即可查看前台页面。

### 4. 管理后台

访问 http://localhost:5000/admin

- 默认用户名：`admin`
- 默认密码：`admin123`

> ⚠️ 生产环境请务必修改默认密码，通过环境变量 `ADMIN_PASSWORD` 设置。

## 配置说明

可通过环境变量或修改 `config.py` 进行配置：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `SECRET_KEY` | Flask 密钥 | 随机生成 |
| `DATABASE_URL` | 数据库连接 | sqlite:///data/dn42_beian.db |
| `ADMIN_PASSWORD` | 管理员密码 | admin123 |
| `REGISTRY_REPO_URL` | Registry 仓库地址 | https://git.dn42.dev/dn42/registry.git |
| `REGISTRY_LOCAL_PATH` | 本地仓库路径 | data/registry |

## 定期同步

使用 cron 定时同步数据（建议每小时一次）：

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（每小时整点同步）
0 * * * * cd /path/to/dn42_icp && python scripts/sync_registry.py >> logs/sync.log 2>&1
```

## 项目结构

```
dn42_icp/
├── app/
│   ├── __init__.py          # 应用初始化
│   ├── models.py            # 数据库模型
│   ├── routes.py            # 路由和 API
│   ├── sync.py              # 数据同步模块 (RPSL解析器)
│   ├── templates/           # 模板文件
│   │   ├── base.html
│   │   ├── index.html       # 首页
│   │   ├── search.html      # 搜索页
│   │   ├── detail.html      # 详情页
│   │   ├── browse.html      # 浏览页
│   │   ├── stats.html       # 统计页
│   │   └── admin/           # 管理后台模板
│   └── static/
│       └── css/style.css    # 样式文件
├── data/                    # 数据目录（自动创建）
│   ├── dn42_beian.db        # SQLite 数据库
│   └── registry/            # dn42 Registry 本地仓库
├── scripts/
│   └── sync_registry.py     # 定时同步脚本
├── config.py                # 配置文件
├── requirements.txt         # 依赖列表
├── run.py                   # 启动入口
└── README.md
```

## 支持的对象类型

系统支持解析 dn42 Registry 中的所有对象类型：

| 类型 | 说明 |
|-----|------|
| `aut-num` | 自治系统 (AS) |
| `inetnum` | IPv4 地址段 |
| `inet6num` | IPv6 地址段 |
| `dns` | 域名 (.dn42) |
| `mntner` | 维护者 |
| `person` | 个人联系人 |
| `organisation` | 组织 |
| `role` | 角色联系人 |
| `route` | IPv4 路由 (ROA) |
| `route6` | IPv6 路由 (ROA) |
| `as-set` | AS 集合 |
| `route-set` | 路由集合 |
| `as-block` | AS 号段 |
| `key-cert` | PGP 公钥证书 |
| `telephony` | 电话前缀 |
| `registry` | 注册表元信息 |

## 部署建议

### 生产环境部署

推荐使用 Gunicorn + Nginx：

```bash
# 安装 gunicorn
pip install gunicorn

# 启动
gunicorn -w 4 -b 127.0.0.1:8000 'app:create_app()'
```

### Docker 部署

可自行创建 Dockerfile，基于 Python 3.11+ 镜像构建。

### 反向代理配置（Nginx）

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 数据来源

所有数据来源于 [dn42 Registry](https://git.dn42.dev/dn42/registry)，遵循 dn42 社区的资源分配政策。

系统仅提供查询和展示功能，不参与资源分配。如需注册 AS 号、IP 段或域名，请按照 dn42 官方流程提交 Pull Request。

## 参考链接

- [dn42 官方网站](https://dn42.dev/)
- [dn42 Wiki](https://wiki.dn42.us/)
- [dn42 Registry](https://git.dn42.dev/dn42/registry)
- [burble.dn42 Explorer](https://explorer.burble.com/)
- [萌国ICP备案](https://icp.gov.moe/)

## 许可证

MIT License
