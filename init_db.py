import sys
import os
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
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                address='Администраторский адрес'
            )
            db.session.add(admin)
            print("✅ Администратор создан: admin / admin123")
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
                    created_at=datetime.utcnow()
                ),
                # ... остальные товары ...
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
