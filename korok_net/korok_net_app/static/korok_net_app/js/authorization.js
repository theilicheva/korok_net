        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('auth-form');
            const usernameInput = document.getElementById('login');
            const passwordInput = document.getElementById('password');
            const submitBtn = document.getElementById('auth-btn');

            // Валидация логина в реальном времени
            usernameInput.addEventListener('blur', function() {
                validateField(this, 'username_error', 'Логин не может быть пустым');
            });

            // Валидация пароля в реальном времени
            passwordInput.addEventListener('blur', function() {
                validateField(this, 'password_error', 'Пароль не может быть пустым');
            });

            // Валидация при вводе (убираем ошибку когда пользователь начинает исправлять)
            usernameInput.addEventListener('input', function() {
                clearFieldError(this, 'username_error');
            });

            passwordInput.addEventListener('input', function() {
                clearFieldError(this, 'password_error');
            });

            // AJAX отправка формы
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                submitLoginForm();
            });
        });

        // Базовая валидация поля
        function validateField(input, errorId, errorMessage) {
            if (!input.value.trim()) {
                showError(errorId, errorMessage);
                input.classList.add('error');
                input.classList.remove('success');
                return false;
            } else {
                clearError(errorId);
                input.classList.remove('error');
                input.classList.add('success');
                return true;
            }
        }

        // Очистка ошибки поля
        function clearFieldError(input, errorId) {
            if (input.value.trim()) {
                clearError(errorId);
                input.classList.remove('error');
            }
        }

        // AJAX отправка формы авторизации
        function submitLoginForm() {
            const form = document.getElementById('auth-form');
            const formData = new FormData(form);
            const submitBtn = document.getElementById('auth-btn');

            // Предварительная валидация
            const isUsernameValid = validateField(
                document.getElementById('login'),
                'username_error',
                'Логин не может быть пустым'
            );

            const isPasswordValid = validateField(
                document.getElementById('password'),
                'password_error',
                'Пароль не может быть пустым'
            );

            if (!isUsernameValid || !isPasswordValid) {
                showError('form-messages', 'Заполните все обязательные поля');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Вход...';

            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccess('form-messages', data.message || 'Авторизация успешна!');

                    // Перенаправление после успешной авторизации
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 1000);

                } else {
                    // Обработка ошибок сервера
                    showFormErrors(data.errors);

                    if (data.errors && data.errors.__all__) {
                        showError('form-messages', data.errors.__all__[0]);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError('form-messages', 'Ошибка сети. Попробуйте еще раз.');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Войти';
            });
        }

        // Показать ошибки формы
        function showFormErrors(errors) {
            // Очищаем все ошибки
            document.querySelectorAll('.error-message').forEach(el => {
                el.textContent = '';
                el.style.display = 'none';
            });

            document.querySelectorAll('.form-input').forEach(input => {
                input.classList.remove('error');
            });

            // Показываем новые ошибки
            for (const field in errors) {
                let errorId;

                // Сопоставляем имена полей с ID ошибок
                if (field === 'username') {
                    errorId = 'username_error';
                } else if (field === 'password') {
                    errorId = 'password_error';
                } else if (field === '__all__') {
                    // Общие ошибки (например, неверный логин/пароль)
                    showError('form-messages', errors[field][0]);
                    continue;
                } else {
                    continue;
                }

                const errorDiv = document.getElementById(errorId);
                if (errorDiv) {
                    errorDiv.textContent = errors[field][0];
                    errorDiv.style.display = 'block';

                    // Подсвечиваем соответствующее поле
                    const fieldId = `id_${field}`;
                    const fieldInput = document.getElementById(fieldId);
                    if (fieldInput) {
                        fieldInput.classList.add('error');
                        fieldInput.classList.remove('success');
                    }
                }
            }
        }

        // Вспомогательные функции
        function showError(elementId, message) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = message;
                element.style.display = 'block';
                element.className = 'error-message';
            }
        }

        function showSuccess(elementId, message) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = message;
                element.style.display = 'block';
                element.className = 'success-message';
            }
        }

        function clearError(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = '';
                element.style.display = 'none';
            }
        }