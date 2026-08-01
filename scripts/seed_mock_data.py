"""
生成模拟数据用于UI测试
Usage: python scripts/seed_mock_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, RegistryObject, SyncRecord, User
from datetime import datetime, timedelta
import random

app = create_app()

def generate_mock_data():
    with app.app_context():
        # 清空现有数据
        RegistryObject.query.delete()
        SyncRecord.query.delete()
        db.session.commit()
        
        # 添加同步记录
        sync_records = [
            SyncRecord(
                status='success',
                message='全量同步完成，共处理 2847 条记录',
                total_objects=2847,
                sync_time=datetime.utcnow() - timedelta(hours=2)
            ),
            SyncRecord(
                status='success',
                message='增量同步完成，更新 156 条记录',
                total_objects=2847,
                sync_time=datetime.utcnow() - timedelta(hours=6)
            ),
            SyncRecord(
                status='success',
                message='全量同步完成，共处理 2801 条记录',
                total_objects=2801,
                sync_time=datetime.utcnow() - timedelta(days=1)
            ),
        ]
        db.session.add_all(sync_records)
        
        # 生成模拟的AS号数据
        as_data = [
            ('AS4242420001', 'Alice Network', 'ALICE-MNT', 'ALICE-DN42', 128),
            ('AS4242420002', 'Bob Internet Services', 'BOB-MNT', 'BOB-DN42', 256),
            ('AS4242420003', 'Charlie Telecom', 'CHARLIE-MNT', 'CHARLIE-DN42', 89),
            ('AS4242420004', 'Delta Networks', 'DELTA-MNT', 'DELTA-DN42', 167),
            ('AS4242420005', 'Echo ISP', 'ECHO-MNT', 'ECHO-DN42', 312),
            ('AS4242420006', 'Foxtrot Fiber', 'FOXTROT-MNT', 'FOXTROT-DN42', 78),
            ('AS4242420007', 'Golf Global', 'GOLF-MNT', 'GOLF-DN42', 201),
            ('AS4242420008', 'Hotel Hosting', 'HOTEL-MNT', 'HOTEL-DN42', 145),
            ('AS4242420009', 'India Infotech', 'INDIA-MNT', 'INDIA-DN42', 67),
            ('AS4242420010', 'Juliett Jumbo', 'JULIETT-MNT', 'JULIETT-DN42', 189),
            ('AS4242420100', 'MikroTik Test Network', 'MIKROTIK-MNT', 'MIKROTIK-DN42', 523),
            ('AS4242420200', 'Neo Network Lab', 'NEO-MNT', 'NEO-DN42', 412),
            ('AS4242420300', 'Omega Operations', 'OMEGA-MNT', 'OMEGA-DN42', 278),
            ('AS4242421000', 'BURBLE-MNT', 'burble.dn42', 'BURBLE-MNT', 892),
        ]
        
        for as_num, name, mnt, admin_c, views in as_data:
            content = f"""aut-num:        {as_num}
as-name:        {name}
descr:          {name} - dn42 autonomous system
admin-c:        {admin_c}
tech-c:         {admin_c}
mnt-by:         {mnt}
mnt-routes:     {mnt}
org:            ORG-{as_num[2:]}
source:         DN42
"""
            obj = RegistryObject(
                obj_type='aut-num',
                obj_key=as_num,
                obj_name=name,
                mnt_by=mnt,
                admin_c=admin_c,
                tech_c=admin_c,
                content=content,
                view_count=views,
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            )
            db.session.add(obj)
        
        # 生成IPv4地址段
        ipv4_data = [
            ('172.20.0.0/16', 'DN42 Network Core', 'DN42-MNT', 45),
            ('172.20.1.0/24', 'Alice Network', 'ALICE-MNT', 23),
            ('172.20.2.0/24', 'Bob Internet', 'BOB-MNT', 18),
            ('172.20.3.0/24', 'Charlie Telecom', 'CHARLIE-MNT', 12),
            ('172.20.4.0/22', 'Delta Networks', 'DELTA-MNT', 34),
            ('172.20.10.0/24', 'Echo ISP', 'ECHO-MNT', 28),
            ('172.21.0.0/16', 'Foxtrot Region', 'FOXTROT-MNT', 56),
            ('172.22.0.0/15', 'Golf Global Range', 'GOLF-MNT', 67),
            ('10.100.0.0/16', 'Hotel Hosting', 'HOTEL-MNT', 41),
            ('10.127.0.0/16', 'India Infotech', 'INDIA-MNT', 19),
        ]
        
        for cidr, name, mnt, views in ipv4_data:
            content = f"""inetnum:        {cidr}
netname:        {name.replace(' ', '-').upper()}
descr:          {name}
country:        DN42
admin-c:        TEST-DN42
tech-c:         TEST-DN42
mnt-by:         {mnt}
status:         ASSIGNED
source:         DN42
"""
            obj = RegistryObject(
                obj_type='inetnum',
                obj_key=cidr,
                obj_name=name,
                mnt_by=mnt,
                content=content,
                view_count=views,
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 120))
            )
            db.session.add(obj)
        
        # 生成IPv6地址段
        ipv6_data = [
            ('fd00::/8', 'DN42 ULA Space', 'DN42-MNT', 23),
            ('fd42:abcd::/32', 'Alice IPv6 Network', 'ALICE-MNT', 15),
            ('fd42:1234::/32', 'Bob IPv6 Services', 'BOB-MNT', 11),
            ('fd42:5678::/32', 'Charlie IPv6', 'CHARLIE-MNT', 9),
            ('fd42:c0de::/32', 'Delta Code Net', 'DELTA-MNT', 18),
            ('fd42:echo::/32', 'Echo ISP v6', 'ECHO-MNT', 14),
        ]
        
        for cidr, name, mnt, views in ipv6_data:
            content = f"""inet6num:       {cidr}
netname:        {name.replace(' ', '-').upper()}-V6
descr:          {name}
country:        DN42
admin-c:        TEST-DN42
tech-c:         TEST-DN42
mnt-by:         {mnt}
status:         ASSIGNED
source:         DN42
"""
            obj = RegistryObject(
                obj_type='inet6num',
                obj_key=cidr,
                obj_name=name,
                mnt_by=mnt,
                content=content,
                view_count=views,
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 100))
            )
            db.session.add(obj)
        
        # 生成域名
        dns_data = [
            ('alice.dn42', 'Alice Network Domain', 'ALICE-MNT', 156),
            ('bob.dn42', 'Bob Internet Domain', 'BOB-MNT', 134),
            ('charlie.dn42', 'Charlie Telecom', 'CHARLIE-MNT', 98),
            ('delta.dn42', 'Delta Networks', 'DELTA-MNT', 112),
            ('echo.dn42', 'Echo ISP', 'ECHO-MNT', 87),
            ('foxtrot.dn42', 'Foxtrot Fiber', 'FOXTROT-MNT', 65),
            ('golf.dn42', 'Golf Global', 'GOLF-MNT', 78),
            ('hotel.dn42', 'Hotel Hosting', 'HOTEL-MNT', 54),
            ('india.dn42', 'India Infotech', 'INDIA-MNT', 43),
            ('juliett.dn42', 'Juliett Jumbo', 'JULIETT-MNT', 32),
            ('mikrotik.dn42', 'MikroTik Test', 'MIKROTIK-MNT', 245),
            ('neo.dn42', 'Neo Network Lab', 'NEO-MNT', 189),
            ('omega.dn42', 'Omega Operations', 'OMEGA-MNT', 167),
            ('burble.dn42', 'burble services', 'BURBLE-MNT', 534),
            ('registry.dn42', 'DN42 Registry', 'DN42-MNT', 421),
        ]
        
        for domain, name, mnt, views in dns_data:
            content = f"""domain:         {domain}
descr:          {name}
admin-c:        TEST-DN42
tech-c:         TEST-DN42
mnt-by:         {mnt}
nserver:        ns1.{domain}
nserver:        ns2.{domain}
source:         DN42
"""
            obj = RegistryObject(
                obj_type='dns',
                obj_key=domain,
                obj_name=name,
                mnt_by=mnt,
                content=content,
                view_count=views,
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 80))
            )
            db.session.add(obj)
        
        # 生成维护者
        mntner_data = [
            ('ALICE-MNT', 'Alice Maintainer', 'alice@example.com', 234),
            ('BOB-MNT', 'Bob Maintainer', 'bob@example.com', 198),
            ('CHARLIE-MNT', 'Charlie Maintainer', 'charlie@example.com', 145),
            ('DELTA-MNT', 'Delta Maintainer', 'delta@example.com', 167),
            ('ECHO-MNT', 'Echo Maintainer', 'echo@example.com', 123),
            ('FOXTROT-MNT', 'Foxtrot Maintainer', 'foxtrot@example.com', 89),
            ('GOLF-MNT', 'Golf Maintainer', 'golf@example.com', 156),
            ('HOTEL-MNT', 'Hotel Maintainer', 'hotel@example.com', 78),
            ('INDIA-MNT', 'India Maintainer', 'india@example.com', 56),
            ('JULIETT-MNT', 'Juliett Maintainer', 'juliett@example.com', 45),
            ('MIKROTIK-MNT', 'MikroTik Maintainer', 'mikrotik@example.com', 312),
            ('BURBLE-MNT', 'burble maintainer', 'burble@burble.dn42', 678),
            ('DN42-MNT', 'DN42 Registry Maintainer', 'registry@dn42.example', 892),
        ]
        
        for mnt, name, email, views in mntner_data:
            content = f"""mntner:         {mnt}
descr:          {name}
admin-c:        {mnt.replace('-MNT', '-DN42')}
upd-to:         {email}
auth:           ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...
mnt-by:         {mnt}
source:         DN42
"""
            obj = RegistryObject(
                obj_type='mntner',
                obj_key=mnt,
                obj_name=name,
                mnt_by=mnt,
                content=content,
                view_count=views,
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 200))
            )
            db.session.add(obj)
        
        # 生成个人联系人
        person_data = [
            ('ALICE-DN42', 'Alice Wang', 'alice@example.com', 'ALICE-MNT', 89),
            ('BOB-DN42', 'Bob Zhang', 'bob@example.com', 'BOB-MNT', 76),
            ('CHARLIE-DN42', 'Charlie Li', 'charlie@example.com', 'CHARLIE-MNT', 54),
            ('DELTA-DN42', 'Delta Chen', 'delta@example.com', 'DELTA-MNT', 67),
            ('ECHO-DN42', 'Echo Liu', 'echo@example.com', 'ECHO-MNT', 43),
            ('NEO-DN42', 'Neo Zhao', 'neo@example.com', 'NEO-MNT', 123),
            ('BURBLE-DN42', 'burble', 'burble@burble.dn42', 'BURBLE-MNT', 345),
        ]
        
        for nic, name, email, mnt, views in person_data:
            content = f"""person:         {name}
nic-hdl:        {nic}
e-mail:         {email}
mnt-by:         {mnt}
source:         DN42
"""
            obj = RegistryObject(
                obj_type='person',
                obj_key=nic,
                obj_name=name,
                mnt_by=mnt,
                content=content,
                view_count=views,
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 150))
            )
            db.session.add(obj)
        
        # 生成组织
        org_data = [
            ('ORG-ALICE', 'Alice Network Organization', 'ALICE-MNT', 67),
            ('ORG-BOB', 'Bob Internet Group', 'BOB-MNT', 54),
            ('ORG-CHARLIE', 'Charlie Telecom Inc', 'CHARLIE-MNT', 45),
            ('ORG-DELTA', 'Delta Networks Ltd', 'DELTA-MNT', 38),
            ('ORG-MIKROTIK', 'MikroTik Test Org', 'MIKROTIK-MNT', 89),
        ]
        
        for org, name, mnt, views in org_data:
            content = f"""organisation:   {org}
org-name:       {name}
descr:          {name}
admin-c:        TEST-DN42
tech-c:         TEST-DN42
mnt-by:         {mnt}
source:         DN42
"""
            obj = RegistryObject(
                obj_type='organisation',
                obj_key=org,
                obj_name=name,
                mnt_by=mnt,
                content=content,
                view_count=views,
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 180))
            )
            db.session.add(obj)
        
        # 生成路由
        route_data = [
            ('172.20.1.0/24', 'AS4242420001', 'ALICE-MNT', 34),
            ('172.20.2.0/24', 'AS4242420002', 'BOB-MNT', 28),
            ('172.20.3.0/24', 'AS4242420003', 'CHARLIE-MNT', 21),
            ('172.20.4.0/22', 'AS4242420004', 'DELTA-MNT', 39),
            ('172.20.10.0/24', 'AS4242420005', 'ECHO-MNT', 25),
            ('172.21.0.0/16', 'AS4242420006', 'FOXTROT-MNT', 45),
            ('10.100.0.0/16', 'AS4242420008', 'HOTEL-MNT', 32),
        ]
        
        for cidr, origin, mnt, views in route_data:
            content = f"""route:          {cidr}
origin:         {origin}
descr:          {origin} route
mnt-by:         {mnt}
source:         DN42
"""
            obj = RegistryObject(
                obj_type='route',
                obj_key=cidr,
                obj_name=f'{cidr} via {origin}',
                mnt_by=mnt,
                content=content,
                view_count=views,
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 90))
            )
            db.session.add(obj)
        
        # 生成IPv6路由
        route6_data = [
            ('fd42:abcd::/32', 'AS4242420001', 'ALICE-MNT', 18),
            ('fd42:1234::/32', 'AS4242420002', 'BOB-MNT', 15),
            ('fd42:c0de::/32', 'AS4242420004', 'DELTA-MNT', 22),
        ]
        
        for cidr, origin, mnt, views in route6_data:
            content = f"""route6:         {cidr}
origin:         {origin}
descr:          {origin} IPv6 route
mnt-by:         {mnt}
source:         DN42
"""
            obj = RegistryObject(
                obj_type='route6',
                obj_key=cidr,
                obj_name=f'{cidr} via {origin}',
                mnt_by=mnt,
                content=content,
                view_count=views,
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 70))
            )
            db.session.add(obj)
        
        db.session.commit()
        
        # 统计
        total = RegistryObject.query.count()
        print(f"✅ 模拟数据生成完成！")
        print(f"   总记录数: {total}")
        print(f"   自治系统: {RegistryObject.query.filter_by(obj_type='aut-num').count()}")
        print(f"   IPv4地址段: {RegistryObject.query.filter_by(obj_type='inetnum').count()}")
        print(f"   IPv6地址段: {RegistryObject.query.filter_by(obj_type='inet6num').count()}")
        print(f"   域名: {RegistryObject.query.filter_by(obj_type='dns').count()}")
        print(f"   维护者: {RegistryObject.query.filter_by(obj_type='mntner').count()}")
        print(f"   个人联系人: {RegistryObject.query.filter_by(obj_type='person').count()}")
        print(f"   组织: {RegistryObject.query.filter_by(obj_type='organisation').count()}")
        print(f"   IPv4路由: {RegistryObject.query.filter_by(obj_type='route').count()}")
        print(f"   IPv6路由: {RegistryObject.query.filter_by(obj_type='route6').count()}")
        print(f"   同步记录: {SyncRecord.query.count()}")

if __name__ == '__main__':
    generate_mock_data()
