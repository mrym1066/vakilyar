import os
import shutil
import datetime
from django.conf import settings


def get_backup_dir():
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def create_backup():
    backup_dir = get_backup_dir()
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    # مسیر دیتابیس SQLite
    db_path = settings.DATABASES['default']['NAME']

    if not os.path.exists(db_path):
        return None, 'فایل دیتابیس یافت نشد.'

    backup_filename = f'vakilyar_backup_{timestamp}.sqlite3'
    backup_path = os.path.join(backup_dir, backup_filename)

    shutil.copy2(db_path, backup_path)

    return backup_path, backup_filename


def get_all_backups():
    backup_dir = get_backup_dir()
    files = []
    for f in os.listdir(backup_dir):
        if f.endswith('.sqlite3'):
            full_path = os.path.join(backup_dir, f)
            size_kb = round(os.path.getsize(full_path) / 1024, 1)
            created = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
            files.append({
                'name': f,
                'size_kb': size_kb,
                'created': created.strftime('%Y-%m-%d %H:%M:%S'),
            })
    return sorted(files, key=lambda x: x['created'], reverse=True)


def delete_backup(filename):
    backup_dir = get_backup_dir()
    file_path = os.path.join(backup_dir, filename)
    if os.path.exists(file_path) and filename.endswith('.sqlite3'):
        os.remove(file_path)
        return True
    return False