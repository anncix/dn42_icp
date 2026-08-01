from flask import Flask
from flask_login import LoginManager, current_user
from config import Config
from .models import db, User, SyncRecord
from werkzeug.security import generate_password_hash
import os

login_manager = LoginManager()
login_manager.login_view = 'admin.login'


def create_app():
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    # 注册蓝图
    from .routes import main, api, admin
    app.register_blueprint(main, url_prefix='/')
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(admin, url_prefix='/admin')
    
    # 全局上下文处理器
    @app.context_processor
    def inject_global_vars():
        last_sync = SyncRecord.query.filter_by(status='success').order_by(
            SyncRecord.sync_time.desc()
        ).first()
        return {
            'last_sync': last_sync,
        }
    
    # 确保数据目录存在
    os.makedirs(os.path.join(app.root_path, '..', 'data'), exist_ok=True)
    
    # 创建数据库表和默认管理员
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员
        admin_user = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
        if not admin_user:
            admin_user = User(
                username=Config.ADMIN_USERNAME,
                password_hash=generate_password_hash(Config.ADMIN_PASSWORD),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
    
    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
