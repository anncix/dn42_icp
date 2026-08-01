from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class RegistryObject(db.Model):
    """dn42 Registry 对象表"""
    __tablename__ = 'registry_objects'
    
    id = db.Column(db.Integer, primary_key=True)
    obj_type = db.Column(db.String(32), index=True)  # 对象类型：aut-num, inetnum, inet6num, dns, mntner, person 等
    obj_key = db.Column(db.String(256), index=True)  # 对象主键：AS4242420001, 172.20.0.0_16 等
    obj_name = db.Column(db.String(256))  # 名称/描述
    content = db.Column(db.Text)  # 完整 RPSL 内容
    mnt_by = db.Column(db.String(128), index=True)  # 维护者
    admin_c = db.Column(db.String(128))  # 管理员联系人
    tech_c = db.Column(db.String(128))  # 技术联系人
    org = db.Column(db.String(128))  # 组织
    source = db.Column(db.String(32), default='DN42')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)  # 访问次数
    
    __table_args__ = (
        db.UniqueConstraint('obj_type', 'obj_key', name='uq_type_key'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'obj_type': self.obj_type,
            'obj_key': self.obj_key,
            'obj_name': self.obj_name,
            'mnt_by': self.mnt_by,
            'admin_c': self.admin_c,
            'tech_c': self.tech_c,
            'org': self.org,
            'source': self.source,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'view_count': self.view_count,
            'content': self.content
        }


class SyncRecord(db.Model):
    """同步记录表"""
    __tablename__ = 'sync_records'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_time = db.Column(db.DateTime, default=datetime.utcnow)
    total_objects = db.Column(db.Integer, default=0)
    added_count = db.Column(db.Integer, default=0)
    updated_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(32), default='success')  # success, failed, running
    message = db.Column(db.Text)
    commit_hash = db.Column(db.String(64))
    
    def to_dict(self):
        return {
            'id': self.id,
            'sync_time': self.sync_time.isoformat() if self.sync_time else None,
            'total_objects': self.total_objects,
            'added_count': self.added_count,
            'updated_count': self.updated_count,
            'status': self.status,
            'message': self.message,
            'commit_hash': self.commit_hash
        }


class SiteConfig(db.Model):
    """站点配置"""
    __tablename__ = 'site_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(64), unique=True, index=True)
    config_value = db.Column(db.Text)
    description = db.Column(db.String(256))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(UserMixin, db.Model):
    """管理员用户"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ICPFilings(db.Model):
    """DN42 ICP 备案表"""
    __tablename__ = 'icp_filings'
    
    id = db.Column(db.Integer, primary_key=True)
    filing_number = db.Column(db.String(32), unique=True, index=True)  # 备案号：DN42-ICP-XXXXXX
    status = db.Column(db.String(16), default='pending', index=True)  # pending/approved/rejected/revoked
    
    # 主体信息
    subject_type = db.Column(db.String(16), default='personal')  # personal / organization
    subject_name = db.Column(db.String(128))  # 主体名称（个人/组织名）
    contact_email = db.Column(db.String(128))  # 联系邮箱
    mntner = db.Column(db.String(64), index=True)  # 对应的 dn42 维护者
    as_number = db.Column(db.String(32), index=True)  # 对应的 AS 号
    
    # 网站信息
    site_name = db.Column(db.String(128))  # 网站名称
    site_url = db.Column(db.String(256))  # 网站地址
    site_desc = db.Column(db.Text)  # 网站简介
    domain = db.Column(db.String(128), index=True)  # 域名
    
    # 其他
    ip_addresses = db.Column(db.Text)  # 服务器IP（逗号分隔）
    remarks = db.Column(db.Text)  # 备注
    
    # 审核
    review_note = db.Column(db.Text)  # 审核意见
    reviewed_at = db.Column(db.DateTime)  # 审核时间
    reviewed_by = db.Column(db.String(64))  # 审核人
    
    # 时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filing_number': self.filing_number,
            'status': self.status,
            'subject_type': self.subject_type,
            'subject_name': self.subject_name,
            'contact_email': self.contact_email,
            'mntner': self.mntner,
            'as_number': self.as_number,
            'site_name': self.site_name,
            'site_url': self.site_url,
            'site_desc': self.site_desc,
            'domain': self.domain,
            'ip_addresses': self.ip_addresses,
            'remarks': self.remarks,
            'review_note': self.review_note,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'view_count': self.view_count,
        }
