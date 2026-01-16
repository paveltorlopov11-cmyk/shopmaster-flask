import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Product, CartItem, Order, OrderItem
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_database():
    """Инициализация базы данных - создание таблиц и тестовых данных"""
    
    with app.app_context():
        print("=" * 50)
        print("🚀 НАЧИНАЕМ ИНИЦИАЛИЗАЦИЮ БАЗЫ ДАННЫХ")
        print("=" * 50)
        
        # 1. СОЗДАЕМ ВСЕ ТАБЛИЦЫ
        try:
            print("📊 Создаем таблицы...")
            db.drop_all()  # Очищаем старые таблицы (если есть)
            db.create_all()  # Создаем новые
            print("✅ Таблицы успешно созданы!")
        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")
            return False
        
        # 2. СОЗДАЕМ АДМИНИСТРАТОРА
        try:
            print("\n👤 Создаем администратора...")
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True,
                    address='Администраторский адрес'
                )
                db.session.add(admin)
                print("✅ Администратор создан: admin / admin123")
            else:
                print("⚠️ Администратор уже существует")
        except Exception as e:
            print(f"❌ Ошибка при создании администратора: {e}")
        
        # 3. СОЗДАЕМ ТЕСТОВЫЕ ТОВАРЫ
        try:
            print("\n🛍️ Создаем тестовые товары...")
            
            test_products = [
                Product(
                    name='iPhone 15 Pro Max',
                    description='Смартфон Apple с камерой 48 МП',
                    price=129990,
                    category='Электроника',
                    stock=15,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Samsung Galaxy S24 Ultra',
                    description='Флагманский смартфон Samsung',
                    price=109990,
                    category='Электроника',
                    stock=12,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Ноутбук MacBook Pro 16" M3',
                    description='Мощный ноутбук для работы и творчества',
                    price=249990,
                    category='Электроника',
                    stock=8,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Футболка мужская хлопковая',
                    description='Хлопковая футболка, все размеры',
                    price=1499,
                    category='Одежда',
                    stock=50,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Джинсы Levi\'s 501',
                    description='Классические прямые джинсы',
                    price=6990,
                    category='Одежда',
                    stock=25,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Куртка зимняя',
                    description='Теплая зимняя куртка с мехом',
                    price=12990,
                    category='Одежда',
                    stock=18,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Книга "Python для начинающих"',
                    description='Полное руководство по Python',
                    price=1890,
                    category='Книги',
                    stock=30,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='"Война и мир" Л.Н. Толстой',
                    description='Классика русской литературы',
                    price=890,
                    category='Книги',
                    stock=40,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Холодильник Samsung',
                    description='Двухкамерный холодильник с No Frost',
                    price=64990,
                    category='Бытовая техника',
                    stock=6,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Стиральная машина LG',
                    description='Автоматическая стиральная машина',
                    price=42990,
                    category='Бытовая техника',
                    stock=9,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Пылесос Dyson',
                    description='Беспроводной пылесос с турбощеткой',
                    price=32990,
                    category='Бытовая техника',
                    stock=11,
                    image_filename=None,
                    created_at=datetime.utcnow()
                ),
                Product(
                    name='Наушники Sony WH-1000XM5',
                    description='Беспроводные наушники с шумоподавлением',
                    price=32990,
                    category='Электроника',
                    stock=20,
                    image_filename=None,
                    created_at=datetime.utcnow()
                )
            ]
            
            db.session.add_all(test_products)
            print(f"✅ Создано {len(test_products)} тестовых товаров")
            
        except Exception as e:
            print(f"❌ Ошибка при создании товаров: {e}")
        
        # 4. СОХРАНЯЕМ ВСЕ ИЗМЕНЕНИЯ
        try:
            db.session.commit()
            print("\n💾 Все изменения успешно сохранены в базе данных!")
            print("=" * 50)
            print("🎉 БАЗА ДАННЫХ УСПЕШНО ИНИЦИАЛИЗИРОВАНА!")
            print("=" * 50)
            
            # Показываем статистику
            print("\n📈 СТАТИСТИКА:")
            print(f"   👥 Пользователей: {User.query.count()}")
            print(f"   🛍️  Товаров: {Product.query.count()}")
            print(f"   📦 Заказов: {Order.query.count()}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при сохранении изменений: {e}")
            return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
