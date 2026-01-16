import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import io
from datetime import datetime
from config import Config

app = Flask(__name__)
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'


# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Отношения
    cart_items = db.relationship('CartItem', backref='cart_user', lazy=True)  # Изменено backref
    orders = db.relationship('Order', backref='order_user', lazy=True)  # Изменено backref

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)
    image_filename = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Отношения
    cart_items = db.relationship('CartItem', backref='cart_product', lazy=True)  # Изменено backref


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    product = db.relationship('Product', foreign_keys=[product_id])


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default='pending')
    total_amount = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.Text)
    billing_address = db.Column(db.Text)
    payment_method = db.Column(db.String(100))
    payment_status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'created_at': self.created_at.strftime('%d.%m.%Y %H:%M')
        }


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship('Order', foreign_keys=[order_id])
    product = db.relationship('Product', foreign_keys=[product_id])
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.context_processor
def utility_processor():
    """Добавляет функции в контекст шаблона"""

    def format_price(price):
        try:
            return f"{float(price):,.2f}".replace(',', ' ').replace('.', ',')
        except:
            return str(price)

    return dict(format_price=format_price)
# Routes
@app.route('/')
def index():
    """Главная страница"""
    # Берем товары из разных категорий
    electronics = Product.query.filter_by(category='Электроника').limit(4).all()
    clothing = Product.query.filter_by(category='Одежда').limit(4).all()
    books = Product.query.filter_by(category='Книги').limit(4).all()
    appliances = Product.query.filter_by(category='Бытовая техника').limit(4).all()

    # Новинки (последние добавленные товары)
    new_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()

    # Горячие предложения (товары с акцией) - берем случайные
    featured_products = Product.query.order_by(db.func.random()).limit(8).all()

    # Новинки электроники (первые 2 товара)
    new_electronics = Product.query.filter_by(category='Электроника') \
        .order_by(Product.created_at.desc()) \
        .limit(2).all()

    return render_template('index.html',
                           featured_products=featured_products,
                           new_products=new_products,
                           electronics=electronics,
                           clothing=clothing,
                           books=books,
                           appliances=appliances,
                           new_electronics=new_electronics)


@app.route('/catalog')
def catalog():
    """Страница каталога товаров"""
    category = request.args.get('category')
    search = request.args.get('search')
    sort = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    query = Product.query

    # Фильтрация по категории
    if category:
        query = query.filter_by(category=category)

    # Поиск
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.category.ilike(search_term)
            )
        )

    # Фильтрация по цене
    if min_price:
        try:
            query = query.filter(Product.price >= float(min_price))
        except:
            pass

    if max_price:
        try:
            query = query.filter(Product.price <= float(max_price))
        except:
            pass

    # Сортировка
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'name':
        query = query.order_by(Product.name.asc())
    else:  # newest по умолчанию
        query = query.order_by(Product.created_at.desc())

    products = query.all()

    # Получаем все категории для фильтра
    all_categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in all_categories if c[0]]

    # Подсчет товаров по категориям
    category_counts = {}
    for cat in categories:
        count = Product.query.filter_by(category=cat).count()
        category_counts[cat] = count

    # Общее количество товаров
    total_products = Product.query.count()

    # Популярные товары для боковой панели
    featured_products = Product.query.order_by(db.func.random()).limit(6).all()

    # Функция для удаления фильтров из URL
    def remove_filter(filter_name):
        args = request.args.copy()
        args.pop(filter_name, None)
        return args

    return render_template('catalog.html',
                           products=products,
                           categories=categories,
                           category_counts=category_counts,
                           total_products=total_products,
                           featured_products=featured_products,
                           remove_filter=remove_filter)

@app.route('/product/<int:product_id>', methods=['GET'])
def product_detail(product_id):
    """Страница с подробной информацией о товаре"""
    product = Product.query.get_or_404(product_id)

    # Похожие товары из той же категории
    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(4).all()

    return render_template('product_detail.html',
                           product=product,
                           related_products=related_products)

@app.route('/about')
def about():
    """Страница о компании"""
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Проверка существования пользователя
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('register'))

        # Создание нового пользователя
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Добро пожаловать, {username}!', 'success')
            return redirect(next_page or url_for('index'))

        flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Выход пользователя"""
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/cart')
@login_required
def cart():
    """Корзина товаров"""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Оформление заказа"""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Ваша корзина пуста', 'warning')
        return redirect(url_for('cart'))

    # Проверяем наличие всех товаров
    unavailable_items = []
    for item in cart_items:
        if item.product.stock < item.quantity:
            unavailable_items.append(item.product.name)

    if unavailable_items:
        flash(f'Следующие товары недоступны в нужном количестве: {", ".join(unavailable_items)}', 'danger')
        return redirect(url_for('cart'))

    total = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        try:
            # Получаем данные из формы
            shipping_address = request.form.get('shipping_address', '').strip()
            billing_address = request.form.get('billing_address', shipping_address).strip()
            payment_method = request.form.get('payment_method', 'card')
            notes = request.form.get('notes', '').strip()

            # Валидация
            if not shipping_address:
                flash('Пожалуйста, укажите адрес доставки', 'danger')
                return redirect(url_for('checkout'))

            # Генерируем номер заказа
            order_number = f'ORD-{datetime.now().strftime("%Y%m%d")}-{current_user.id:04d}-{int(datetime.now().timestamp()) % 10000:04d}'

            # Создаем заказ
            order = Order(
                user_id=current_user.id,
                order_number=order_number,
                total_amount=total,
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment_method=payment_method,
                notes=notes
            )
            db.session.add(order)
            db.session.flush()  # Получаем ID заказа

            # Добавляем товары в заказ
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product.id,
                    product_name=cart_item.product.name,
                    product_price=cart_item.product.price,
                    quantity=cart_item.quantity
                )
                db.session.add(order_item)

                # Уменьшаем количество товара на складе
                cart_item.product.stock -= cart_item.quantity

            # Очищаем корзину
            CartItem.query.filter_by(user_id=current_user.id).delete()

            # Сохраняем все изменения
            db.session.commit()

            flash(f'Заказ #{order.order_number} успешно оформлен!', 'success')
            return redirect(url_for('order_confirmation', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Ошибка при оформлении заказа: {e}')
            flash('Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз.', 'danger')

    return render_template('checkout.html',
                           cart_items=cart_items,
                           total=total,
                           user=current_user)


@app.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Страница подтверждения заказа"""
    order = Order.query.get_or_404(order_id)

    # Проверяем, что заказ принадлежит пользователю
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    return render_template('order_confirmation.html', order=order)


@app.route('/orders')
@login_required
def user_orders():
    """Список заказов пользователя"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)


@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """Детальная информация о заказе"""
    order = Order.query.get_or_404(order_id)

    # Проверяем, что заказ принадлежит пользователю
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    return render_template('order_detail.html', order=order)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Добавление товара в корзину"""
    try:
        product = Product.query.get_or_404(product_id)

        # Проверяем наличие товара на складе
        if product.stock <= 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': f'Товар "{product.name}" закончился'
                })
            flash(f'Товар "{product.name}" закончился', 'warning')
            return redirect(request.referrer or url_for('catalog'))

        # Ищем товар в корзине пользователя
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()

        if cart_item:
            # Проверяем, не превышаем ли остаток на складе
            if cart_item.quantity < product.stock:
                cart_item.quantity += 1
                message = f'Количество товара "{product.name}" в корзине увеличено'
                success = True
            else:
                message = f'Невозможно добавить больше товара "{product.name}". На складе осталось только {product.stock} шт.'
                success = False
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product_id)
            db.session.add(cart_item)
            message = f'Товар "{product.name}" добавлен в корзину'
            success = True

        db.session.commit()

        # Подсчитываем общее количество товаров в корзине
        cart_count = sum(item.quantity for item in current_user.cart_items)

        # Проверяем AJAX запрос
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': success,
                'message': message,
                'cart_count': cart_count,
                'product_name': product.name
            })

        # Для обычных POST запросов (без AJAX) - flash сообщение и редирект
        flash(message, 'success' if success else 'warning')
        return redirect(request.referrer or url_for('catalog'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error adding to cart: {e}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'Произошла ошибка при добавлении товара в корзину'
            })

        flash('Произошла ошибка при добавлении товара в корзину', 'danger')
        return redirect(request.referrer or url_for('catalog'))

@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Обновление количества товара в корзине"""
    cart_item = CartItem.query.get_or_404(item_id)

    if cart_item.user_id != current_user.id:
        flash('Ошибка доступа', 'danger')
        return redirect(url_for('cart'))

    action = request.form.get('action')

    if action == 'increment':
        cart_item.quantity += 1
    elif action == 'decrement':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
    elif action == 'remove':
        db.session.delete(cart_item)

    db.session.commit()
    return redirect(url_for('cart'))


@app.route('/clear_cart')
@login_required
def clear_cart():
    """Очистка корзины"""
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Корзина очищена', 'info')
    return redirect(url_for('cart'))


# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    """Админ панель"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    # Статистика
    stats = {
        'users_count': User.query.count(),
        'products_count': Product.query.count(),
        'orders_count': Order.query.count(),
        'pending_orders': Order.query.filter_by(status='pending').count()
    }

    # Последние заказы
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    # Количество ожидающих заказов для боковой панели
    pending_orders = Order.query.filter_by(status='pending').count()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_orders=recent_orders,
                           pending_orders=pending_orders)


@app.route('/admin/users')
@login_required
def admin_users():
    """Управление пользователями"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    users = User.query.all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/products')
@login_required
def admin_products():
    """Управление товарами"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    products = Product.query.all()
    return render_template('admin/products.html', products=products)


@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Добавление товара"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        category = request.form.get('category')
        stock = int(request.form.get('stock'))

        product = Product(
            name=name,
            description=description,
            price=price,
            category=category,
            stock=stock
        )

        # Обработка изображения
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Добавляем timestamp для уникальности
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                product.image_filename = filename

        db.session.add(product)
        db.session.commit()

        flash('Товар успешно добавлен', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html')


@app.route('/admin/product/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    """Редактирование товара"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.category = request.form.get('category')
        product.stock = int(request.form.get('stock'))

        # Обработка нового изображения
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # Удаляем старое изображение если есть
                if product.image_filename:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                product.image_filename = filename

        db.session.commit()
        flash('Товар успешно обновлен', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=product)


@app.route('/admin/product/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    """Удаление товара"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    product = Product.query.get_or_404(id)

    # Удаляем изображение если есть
    if product.image_filename:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], product.image_filename)
        if os.path.exists(filepath):
            os.remove(filepath)

    # Удаляем связанные записи в корзине
    CartItem.query.filter_by(product_id=id).delete()

    db.session.delete(product)
    db.session.commit()

    flash('Товар успешно удален', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/user/toggle_admin/<int:id>', methods=['POST'])
@login_required
def toggle_admin(id):
    """Изменение статуса администратора"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    user = User.query.get_or_404(id)

    # Нельзя изменить свой собственный статус
    if user.id == current_user.id:
        flash('Нельзя изменить свой собственный статус администратора', 'danger')
        return redirect(url_for('admin_users'))

    user.is_admin = not user.is_admin
    db.session.commit()

    status = 'администратором' if user.is_admin else 'пользователем'
    flash(f'Пользователь {user.username} теперь {status}', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/user/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    """Удаление пользователя"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    user = User.query.get_or_404(id)

    # Нельзя удалить себя
    if user.id == current_user.id:
        flash('Нельзя удалить свой собственный аккаунт', 'danger')
        return redirect(url_for('admin_users'))

    # Удаляем корзину пользователя
    CartItem.query.filter_by(user_id=id).delete()

    db.session.delete(user)
    db.session.commit()

    flash('Пользователь успешно удален', 'success')
    return redirect(url_for('admin_users'))


# Админ маршруты для заказов
@app.route('/admin/orders')
@login_required
def admin_orders():
    """Управление заказами в админ-панели"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    # Получаем параметры фильтрации
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')

    # Базовый запрос
    query = Order.query

    # Фильтрация по статусу
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    # Поиск
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Order.order_number.ilike(search_term),
                Order.shipping_address.ilike(search_term),
                Order.user.has(User.username.ilike(search_term)),
                Order.user.has(User.email.ilike(search_term))
            )
        )

    # Сортировка
    orders = query.order_by(Order.created_at.desc()).all()

    # Статистика
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    processing_orders = Order.query.filter_by(status='processing').count()
    completed_orders = Order.query.filter_by(status='delivered').count()

    return render_template('admin/orders.html',
                           orders=orders,
                           total_orders=total_orders,
                           pending_orders=pending_orders,
                           processing_orders=processing_orders,
                           completed_orders=completed_orders,
                           status_filter=status_filter,
                           search=search)


@app.route('/admin/order/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    """Детальная информация о заказе в админ-панели"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)


@app.route('/admin/order/update_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    """Обновление статуса заказа"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    if new_status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        order.status = new_status
        order.updated_at = datetime.utcnow()

        # Если заказ отменен, возвращаем товары на склад
        if new_status == 'cancelled' and order.status != 'cancelled':
            for item in order.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock += item.quantity

        db.session.commit()
        flash(f'Статус заказа #{order.order_number} обновлен на "{new_status}"', 'success')
    else:
        flash('Недопустимый статус', 'danger')

    return redirect(url_for('admin_order_detail', order_id=order_id))


@app.route('/admin/order/update_payment/<int:order_id>', methods=['POST'])
@login_required
def update_order_payment(order_id):
    """Обновление статуса оплаты"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    order = Order.query.get_or_404(order_id)
    new_payment_status = request.form.get('payment_status')

    if new_payment_status in ['pending', 'paid', 'failed']:
        order.payment_status = new_payment_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Статус оплаты заказа #{order.order_number} обновлен', 'success')
    else:
        flash('Недопустимый статус оплаты', 'danger')

    return redirect(url_for('admin_order_detail', order_id=order_id))


@app.route('/admin/order/delete/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    """Удаление заказа"""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    order = Order.query.get_or_404(order_id)
    order_number = order.order_number

    try:
        # Возвращаем товары на склад если заказ не был отменен ранее
        if order.status != 'cancelled':
            for item in order.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock += item.quantity

        db.session.delete(order)
        db.session.commit()
        flash(f'Заказ #{order_number} успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении заказа: {str(e)}', 'danger')

    return redirect(url_for('admin_orders'))

# API для получения товаров в формате JSON
@app.route('/api/products')
def api_products():
    """API для получения списка товаров"""
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])


@app.route('/api/products/<int:id>')
def api_product(id):
    """API для получения конкретного товара"""
    product = Product.query.get_or_404(id)
    return jsonify(product.to_dict())

# Переменная для отслеживания инициализации
_db_initialized = False

@app.before_request
def initialize_database_on_first_request():
    """Инициализация базы данных при первом запросе"""
    global _db_initialized
    
    if not _db_initialized:
        try:
            print("🔄 Проверяем базу данных при первом запросе...")
            
            with app.app_context():
                # Проверяем существует ли таблица product
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                
                if 'product' not in inspector.get_table_names():
                    print("📦 Создаем таблицы...")
                    db.create_all()
                    
                    # Создаем админа
                    from werkzeug.security import generate_password_hash
                    admin = User(
                        username='admin',
                        email='admin@example.com',
                        password_hash=generate_password_hash('admin123'),
                        is_admin=True
                    )
                    db.session.add(admin)
                    
                    # Минимальные тестовые товары
                    from datetime import datetime
                    products = [
                        Product(name='iPhone 15', price=89990, category='Электроника', stock=10, created_at=datetime.utcnow()),
                        Product(name='Ноутбук Asus', price=64990, category='Электроника', stock=5, created_at=datetime.utcnow()),
                        Product(name='Футболка', price=1990, category='Одежда', stock=50, created_at=datetime.utcnow()),
                        Product(name='Книга Python', price=1590, category='Книги', stock=25, created_at=datetime.utcnow()),
                    ]
                    
                    for product in products:
                        db.session.add(product)
                    
                    db.session.commit()
                    print("✅ База данных инициализирована!")
                else:
                    print("✅ Таблицы уже существуют")
            
            _db_initialized = True
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации: {e}")
            # Не помечаем как инициализированную, чтобы попробовать снова

# Обработчики ошибок
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # Логируем ошибку для отладки
    app.logger.error(f'Server Error: {e}', exc_info=True)
    return render_template('500.html', error=str(e)), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Логируем все необработанные исключения
    app.logger.error(f'Unhandled Exception: {e}', exc_info=True)
    return render_template('500.html', error=str(e)), 500

# Создание первого администратора
# Добавьте эту функцию для создания админа
def create_admin():
    with app.app_context():
        admin_exists = User.query.filter_by(username='admin').first()
        if not admin_exists:
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin123')
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            print('Администратор создан: admin / admin123')

# Функция для инициализации базы данных
def init_database():
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        print("✅ Таблицы созданы/проверены")
        
        # Создаем администратора если его нет
        admin_exists = User.query.filter_by(username='admin').first()
        if not admin_exists:
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin123')
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            print('✅ Администратор создан: admin / admin123')
        
        # Добавляем тестовые товары если их нет
        if Product.query.count() == 0:
            test_products = [
                Product(
                    name='Смартфон Samsung Galaxy S23',
                    description='Новый флагманский смартфон с камерой 200MP',
                    price=89999.99,
                    category='Электроника',
                    stock=15,
                    image_filename='phone.jpg'
                ),
                Product(
                    name='Ноутбук Apple MacBook Pro 16',
                    description='Мощный ноутбук для профессионалов',
                    price=249999.99,
                    category='Электроника',
                    stock=8
                ),
                Product(
                    name='Футболка мужская',
                    description='Хлопковая футболка, размеры M-XXL',
                    price=1999.99,
                    category='Одежда',
                    stock=50
                ),
                Product(
                    name='Книга "Мастер и Маргарита"',
                    description='Классика русской литературы',
                    price=599.99,
                    category='Книги',
                    stock=25
                ),
                Product(
                    name='Холодильник Samsung',
                    description='Двухкамерный холодильник с No Frost',
                    price=64999.99,
                    category='Бытовая техника',
                    stock=5
                )
            ]
            
            for product in test_products:
                db.session.add(product)
            
            db.session.commit()
            print(f"✅ Добавлено {len(test_products)} тестовых товаров")

# Вызываем инициализацию при запуске
if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
