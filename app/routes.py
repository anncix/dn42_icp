from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, RegistryObject, SyncRecord, User
from .sync import RegistrySyncer
from config import Config
import os
from sqlalchemy import func, or_, desc

main = Blueprint('main', __name__)
api = Blueprint('api', __name__)
admin = Blueprint('admin', __name__)


# ============ 前端页面路由 ============

@main.route('/')
def index():
    """首页"""
    # 统计数据
    stats = {}
    obj_types = ['aut-num', 'inetnum', 'inet6num', 'dns', 'mntner', 'person', 'route', 'route6', 'organisation']
    for t in obj_types:
        stats[t] = RegistryObject.query.filter_by(obj_type=t).count()
    
    # 最新更新
    recent_updates = RegistryObject.query.order_by(
        RegistryObject.updated_at.desc()
    ).limit(10).all()
    
    # 热门查询（按访问量）
    hot_objects = RegistryObject.query.filter(
        RegistryObject.obj_type.in_(['aut-num', 'dns', 'mntner'])
    ).order_by(
        RegistryObject.view_count.desc()
    ).limit(10).all()
    
    # 最后同步时间
    last_sync = SyncRecord.query.filter_by(status='success').order_by(
        SyncRecord.sync_time.desc()
    ).first()
    
    return render_template('index.html',
                         stats=stats,
                         recent_updates=recent_updates,
                         hot_objects=hot_objects,
                         last_sync=last_sync)


@main.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '').strip()
    obj_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = Config.PER_PAGE
    
    results = []
    total = 0
    
    if query:
        q = RegistryObject.query
        
        # 按类型过滤
        if obj_type != 'all':
            q = q.filter_by(obj_type=obj_type)
        
        # 搜索关键词
        search_pattern = f'%{query}%'
        q = q.filter(or_(
            RegistryObject.obj_key.like(search_pattern),
            RegistryObject.obj_name.like(search_pattern),
            RegistryObject.mnt_by.like(search_pattern),
            RegistryObject.admin_c.like(search_pattern),
            RegistryObject.tech_c.like(search_pattern),
            RegistryObject.content.like(search_pattern),
        ))
        
        total = q.count()
        results = q.order_by(RegistryObject.obj_type, RegistryObject.obj_key).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    # 类型统计
    type_counts = {}
    if query:
        type_query = db.session.query(
            RegistryObject.obj_type,
            func.count(RegistryObject.id)
        ).filter(or_(
            RegistryObject.obj_key.like(search_pattern),
            RegistryObject.obj_name.like(search_pattern),
            RegistryObject.mnt_by.like(search_pattern),
            RegistryObject.content.like(search_pattern),
        )).group_by(RegistryObject.obj_type).all()
        for t, c in type_query:
            type_counts[t] = c
    
    return render_template('search.html',
                         query=query,
                         obj_type=obj_type,
                         results=results,
                         total=total,
                         type_counts=type_counts,
                         page=page,
                         per_page=per_page)


@main.route('/detail/<obj_type>/<path:obj_key>')
def detail(obj_type, obj_key):
    """详情页"""
    obj = RegistryObject.query.filter_by(obj_type=obj_type, obj_key=obj_key).first_or_404()
    
    # 增加访问计数
    obj.view_count += 1
    db.session.commit()
    
    # 解析内容为键值对
    parsed = parse_rpsl_content(obj.content)
    
    # 查找关联对象
    related = {
        'mnt_by': [],
        'admin_c': [],
        'tech_c': [],
        'routes': [],
        'domains': [],
    }
    
    # 查找维护者
    if obj.mnt_by:
        mnt = RegistryObject.query.filter_by(obj_type='mntner', obj_key=obj.mnt_by).first()
        if mnt:
            related['mnt_by'].append(mnt)
    
    # 查找管理员联系人
    if obj.admin_c:
        person = RegistryObject.query.filter(
            (RegistryObject.obj_type == 'person') | (RegistryObject.obj_type == 'role'),
            RegistryObject.obj_key.like(f'%{obj.admin_c}%')
        ).first()
        if person:
            related['admin_c'].append(person)
    
    # 查找技术联系人
    if obj.tech_c:
        person = RegistryObject.query.filter(
            (RegistryObject.obj_type == 'person') | (RegistryObject.obj_type == 'role'),
            RegistryObject.obj_key.like(f'%{obj.tech_c}%')
        ).first()
        if person:
            related['tech_c'].append(person)
    
    # 如果是AS号，查找相关的路由和域名
    if obj_type == 'aut-num':
        as_num = obj_key.replace('AS', '')
        search_as = f'AS{as_num}'
        routes = RegistryObject.query.filter(
            RegistryObject.obj_type.in_(['route', 'route6']),
            RegistryObject.content.like(f'%{search_as}%')
        ).limit(20).all()
        related['routes'] = routes
    
    return render_template('detail.html',
                         obj=obj,
                         parsed=parsed,
                         related=related)


@main.route('/browse/<obj_type>')
def browse(obj_type):
    """按类型浏览"""
    page = request.args.get('page', 1, type=int)
    per_page = Config.PER_PAGE
    sort = request.args.get('sort', 'key')  # key, name, views
    
    valid_types = ['aut-num', 'inetnum', 'inet6num', 'dns', 'mntner', 'person', 
                   'organisation', 'route', 'route6', 'as-set', 'role', 'as-block',
                   'key-cert', 'telephony', 'route-set']
    
    if obj_type not in valid_types:
        return redirect(url_for('main.index'))
    
    query = RegistryObject.query.filter_by(obj_type=obj_type)
    
    # 排序
    if sort == 'name':
        query = query.order_by(RegistryObject.obj_name)
    elif sort == 'views':
        query = query.order_by(RegistryObject.view_count.desc())
    else:
        query = query.order_by(RegistryObject.obj_key)
    
    total = query.count()
    results = query.paginate(page=page, per_page=per_page, error_out=False)
    
    type_names = {
        'aut-num': '自治系统 (AS)',
        'inetnum': 'IPv4 地址段',
        'inet6num': 'IPv6 地址段',
        'dns': '域名',
        'mntner': '维护者',
        'person': '个人联系人',
        'organisation': '组织',
        'route': 'IPv4 路由',
        'route6': 'IPv6 路由',
        'as-set': 'AS 集合',
        'role': '角色联系人',
        'as-block': 'AS 号段',
        'key-cert': '密钥证书',
        'telephony': '电话前缀',
        'route-set': '路由集合',
    }
    
    return render_template('browse.html',
                         obj_type=obj_type,
                         type_name=type_names.get(obj_type, obj_type),
                         results=results,
                         total=total,
                         page=page,
                         per_page=per_page,
                         sort=sort)


@main.route('/stats')
def stats():
    """统计页面"""
    # 各类型数量
    type_stats = db.session.query(
        RegistryObject.obj_type,
        func.count(RegistryObject.id)
    ).group_by(RegistryObject.obj_type).all()
    
    type_stats = sorted(type_stats, key=lambda x: x[1], reverse=True)
    
    # 同步历史
    sync_history = SyncRecord.query.order_by(
        SyncRecord.sync_time.desc()
    ).limit(20).all()
    
    return render_template('stats.html',
                         type_stats=type_stats,
                         sync_history=sync_history)


# ============ API 路由 ============

@api.route('/search')
def api_search():
    """搜索 API"""
    query = request.args.get('q', '').strip()
    obj_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'query parameter required'}), 400
    
    q = RegistryObject.query
    
    if obj_type != 'all':
        q = q.filter_by(obj_type=obj_type)
    
    search_pattern = f'%{query}%'
    q = q.filter(or_(
        RegistryObject.obj_key.like(search_pattern),
        RegistryObject.obj_name.like(search_pattern),
        RegistryObject.mnt_by.like(search_pattern),
        RegistryObject.content.like(search_pattern),
    ))
    
    total = q.count()
    results = q.order_by(RegistryObject.obj_type, RegistryObject.obj_key).limit(per_page).offset((page-1)*per_page).all()
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'results': [r.to_dict() for r in results]
    })


@api.route('/detail/<obj_type>/<path:obj_key>')
def api_detail(obj_type, obj_key):
    """详情 API"""
    obj = RegistryObject.query.filter_by(obj_type=obj_type, obj_key=obj_key).first()
    
    if not obj:
        return jsonify({'error': 'not found'}), 404
    
    # 增加访问计数
    obj.view_count += 1
    db.session.commit()
    
    return jsonify(obj.to_dict())


@api.route('/stats')
def api_stats():
    """统计 API"""
    type_stats = db.session.query(
        RegistryObject.obj_type,
        func.count(RegistryObject.id)
    ).group_by(RegistryObject.obj_type).all()
    
    return jsonify({
        'total': sum(c for _, c in type_stats),
        'by_type': {t: c for t, c in type_stats}
    })


# ============ 管理后台路由 ============

@admin.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        
        flash('用户名或密码错误', 'error')
    
    return render_template('admin/login.html')


@admin.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    return redirect(url_for('main.index'))


@admin.route('/')
@login_required
def dashboard():
    """管理后台首页"""
    # 统计数据
    total_objects = RegistryObject.query.count()
    total_types = db.session.query(func.count(func.distinct(RegistryObject.obj_type))).scalar()
    
    # 最后同步
    last_sync = SyncRecord.query.filter_by(status='success').order_by(
        SyncRecord.sync_time.desc()
    ).first()
    
    # 同步历史
    sync_history = SyncRecord.query.order_by(
        SyncRecord.sync_time.desc()
    ).limit(10).all()
    
    # 各类型数量
    type_stats = db.session.query(
        RegistryObject.obj_type,
        func.count(RegistryObject.id)
    ).group_by(RegistryObject.obj_type).all()
    
    return render_template('admin/dashboard.html',
                         total_objects=total_objects,
                         total_types=total_types,
                         last_sync=last_sync,
                         sync_history=sync_history,
                         type_stats=type_stats)


@admin.route('/sync', methods=['POST'])
@login_required
def sync():
    """手动触发同步"""
    syncer = RegistrySyncer(
        Config.REGISTRY_REPO_URL,
        Config.REGISTRY_LOCAL_PATH
    )
    record = syncer.sync_to_database()
    
    if record.status == 'success':
        flash(f'同步成功：新增 {record.added_count} 条，更新 {record.updated_count} 条', 'success')
    else:
        flash(f'同步失败：{record.message}', 'error')
    
    return redirect(url_for('admin.dashboard'))


@admin.route('/objects')
@login_required
def objects():
    """对象管理"""
    obj_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    q = RegistryObject.query
    
    if obj_type != 'all':
        q = q.filter_by(obj_type=obj_type)
    
    total = q.count()
    results = q.order_by(RegistryObject.obj_type, RegistryObject.obj_key).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/objects.html',
                         results=results,
                         total=total,
                         obj_type=obj_type,
                         page=page,
                         per_page=per_page)


# ============ 工具函数 ============

def parse_rpsl_content(content):
    """解析 RPSL 内容为键值对列表"""
    result = []
    current_key = None
    current_value = []
    
    for line in content.split('\n'):
        if not line or line.startswith('#') or line.startswith('%'):
            continue
        
        # 续行
        if line.startswith(' ') or line.startswith('\t') or line.startswith('+'):
            if current_key:
                current_value.append(line.strip())
            continue
        
        # 保存上一个
        if current_key and current_value:
            result.append({
                'key': current_key,
                'value': '\n'.join(current_value)
            })
        
        # 新字段
        parts = line.split(':', 1)
        if len(parts) == 2:
            current_key = parts[0].strip()
            value = parts[1].strip()
            current_value = [value] if value else []
        else:
            current_key = None
            current_value = []
    
    # 最后一个
    if current_key and current_value:
        result.append({
            'key': current_key,
            'value': '\n'.join(current_value)
        })
    
    return result
