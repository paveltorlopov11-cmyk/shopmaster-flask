import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # PostgreSQL для Render, SQLite для разработки
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///shop.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки для загрузки файлов
    # На Render используем временную папку, локально - постоянную
    if os.environ.get('RENDER'):
        # На Render - временная папка
        UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
    else:
        # Локально - постоянная папка
        UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    
    PRODUCT_IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'products')
    
    # Создаем папки если их нет
    os.makedirs(PRODUCT_IMAGE_FOLDER, exist_ok=True)
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Настройки для продакшн
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    @staticmethod
    def init_app(app):
        pass
