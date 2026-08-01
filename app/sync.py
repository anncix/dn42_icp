import os
import re
import git
from datetime import datetime
from .models import db, RegistryObject, SyncRecord


# dn42 Registry 中的对象类型映射
OBJECT_TYPES = {
    'aut-num': 'aut-num',
    'as-block': 'as-block',
    'as-set': 'as-set',
    'dns': 'dns',
    'domain': 'dns',  # 兼容
    'inetnum': 'inetnum',
    'inet6num': 'inet6num',
    'key-cert': 'key-cert',
    'mntner': 'mntner',
    'organisation': 'organisation',
    'person': 'person',
    'registry': 'registry',
    'role': 'role',
    'route': 'route',
    'route-set': 'route-set',
    'route6': 'route6',
    'schema': 'schema',
    'telephony': 'telephony',
}


class RPSLParser:
    """RPSL 格式解析器"""
    
    @staticmethod
    def parse_file(filepath):
        """解析单个 RPSL 文件"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return RPSLParser.parse_content(content)
    
    @staticmethod
    def parse_content(content):
        """解析 RPSL 内容为字典"""
        result = {}
        current_key = None
        current_value = []
        
        for line in content.split('\n'):
            # 跳过注释和空行
            if not line or line.startswith('#') or line.startswith('%'):
                continue
            
            # 续行（以 + 或空格开头）
            if line.startswith(' ') or line.startswith('\t') or line.startswith('+'):
                if current_key:
                    current_value.append(line.strip())
                continue
            
            # 普通行 key: value
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*:\s*(.*)$', line)
            if match:
                # 保存上一个字段
                if current_key:
                    if current_key in result:
                        if isinstance(result[current_key], list):
                            result[current_key].append('\n'.join(current_value))
                        else:
                            result[current_key] = [result[current_key], '\n'.join(current_value)]
                    else:
                        result[current_key] = '\n'.join(current_value)
                
                current_key = match.group(1).lower()
                value = match.group(2).strip()
                current_value = [value] if value else []
        
        # 保存最后一个字段
        if current_key and current_value:
            if current_key in result:
                if isinstance(result[current_key], list):
                    result[current_key].append('\n'.join(current_value))
                else:
                    result[current_key] = [result[current_key], '\n'.join(current_value)]
            else:
                result[current_key] = '\n'.join(current_value)
        
        return result


class RegistrySyncer:
    """dn42 Registry 同步器"""
    
    def __init__(self, repo_url, local_path):
        self.repo_url = repo_url
        self.local_path = local_path
        self.repo = None
    
    def clone_or_pull(self):
        """克隆或拉取最新代码"""
        if os.path.exists(os.path.join(self.local_path, '.git')):
            self.repo = git.Repo(self.local_path)
            origin = self.repo.remotes.origin
            origin.pull()
        else:
            os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
            self.repo = git.Repo.clone_from(self.repo_url, self.local_path, depth=1)
        
        return self.repo.head.commit.hexsha
    
    def get_data_dir(self):
        """获取 data 目录路径"""
        return os.path.join(self.local_path, 'data')
    
    def scan_objects(self):
        """扫描所有对象文件"""
        data_dir = self.get_data_dir()
        objects = []
        
        if not os.path.exists(data_dir):
            return objects
        
        for type_dir in os.listdir(data_dir):
            type_path = os.path.join(data_dir, type_dir)
            if not os.path.isdir(type_path):
                continue
            
            obj_type = type_dir.lower()
            # 跳过 schema 目录（非数据对象）
            if obj_type == 'schema':
                continue
            
            for filename in os.listdir(type_path):
                filepath = os.path.join(type_path, filename)
                if not os.path.isfile(filepath):
                    continue
                
                try:
                    parsed = RPSLParser.parse_file(filepath)
                    if not parsed:
                        continue
                    
                    obj_key = filename
                    obj_name = self._extract_name(obj_type, parsed)
                    mnt_by = self._get_first_value(parsed.get('mnt-by', ''))
                    admin_c = self._get_first_value(parsed.get('admin-c', ''))
                    tech_c = self._get_first_value(parsed.get('tech-c', ''))
                    org = self._get_first_value(parsed.get('org', ''))
                    source = self._get_first_value(parsed.get('source', 'DN42'))
                    
                    # 读取完整内容
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    objects.append({
                        'obj_type': obj_type,
                        'obj_key': obj_key,
                        'obj_name': obj_name,
                        'content': content,
                        'mnt_by': mnt_by,
                        'admin_c': admin_c,
                        'tech_c': tech_c,
                        'org': org,
                        'source': source,
                    })
                except Exception as e:
                    print(f"Error parsing {filepath}: {e}")
                    continue
        
        return objects
    
    def _extract_name(self, obj_type, parsed):
        """从解析结果中提取名称/描述"""
        # 不同类型的对象有不同的名称字段
        name_fields = {
            'aut-num': ['as-name', 'aut-num'],
            'inetnum': ['netname', 'descr', 'inetnum'],
            'inet6num': ['netname', 'descr', 'inet6num'],
            'dns': ['domain'],
            'mntner': ['mntner'],
            'person': ['person', 'nic-hdl'],
            'organisation': ['org-name', 'organisation'],
            'role': ['role', 'nic-hdl'],
            'route': ['route', 'descr'],
            'route6': ['route6', 'descr'],
            'as-set': ['as-set', 'descr'],
            'route-set': ['route-set', 'descr'],
            'as-block': ['as-block'],
            'key-cert': ['key-cert'],
            'registry': ['registry'],
            'telephony': ['telephony'],
        }
        
        fields = name_fields.get(obj_type, ['descr'])
        for field in fields:
            value = parsed.get(field)
            if value:
                return self._get_first_value(value)
        
        return ''
    
    def _get_first_value(self, value):
        """获取值列表中的第一个值"""
        if isinstance(value, list):
            return value[0] if value else ''
        return value or ''
    
    def sync_to_database(self):
        """同步数据到数据库"""
        record = SyncRecord(status='running')
        db.session.add(record)
        db.session.commit()
        
        try:
            # 拉取最新代码
            commit_hash = self.clone_or_pull()
            
            # 扫描对象
            objects = self.scan_objects()
            
            added = 0
            updated = 0
            
            for obj_data in objects:
                existing = RegistryObject.query.filter_by(
                    obj_type=obj_data['obj_type'],
                    obj_key=obj_data['obj_key']
                ).first()
                
                if existing:
                    # 更新现有记录（保留 view_count）
                    existing.obj_name = obj_data['obj_name']
                    existing.content = obj_data['content']
                    existing.mnt_by = obj_data['mnt_by']
                    existing.admin_c = obj_data['admin_c']
                    existing.tech_c = obj_data['tech_c']
                    existing.org = obj_data['org']
                    existing.source = obj_data['source']
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                else:
                    # 新增记录
                    new_obj = RegistryObject(**obj_data)
                    db.session.add(new_obj)
                    added += 1
            
            db.session.commit()
            
            record.status = 'success'
            record.total_objects = len(objects)
            record.added_count = added
            record.updated_count = updated
            record.commit_hash = commit_hash
            record.message = f'同步成功：新增 {added} 条，更新 {updated} 条，共 {len(objects)} 条'
            
        except Exception as e:
            db.session.rollback()
            record.status = 'failed'
            record.message = f'同步失败：{str(e)}'
        
        db.session.commit()
        return record
