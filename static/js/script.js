// AJAX добавление в корзину
document.addEventListener('DOMContentLoaded', function() {
    // Обработка форм добавления в корзину
    const cartForms = document.querySelectorAll('form[action*="add_to_cart"]');

    cartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const url = this.action;

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Обновляем счетчик корзины
                    const cartCount = document.querySelector('.cart-count');
                    if (cartCount) {
                        cartCount.textContent = data.cart_count;
                    }

                    // Показываем уведомление
                    showNotification(data.message, 'success');
                } else {
                    showNotification(data.message, 'warning');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Если AJAX не работает, отправляем форму обычным способом
                this.submit();
            });
        });
    });

    // Функция показа уведомлений
    function showNotification(message, type) {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Добавляем на страницу
        document.body.appendChild(notification);

        // Автоматически скрываем через 3 секунды
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
});
