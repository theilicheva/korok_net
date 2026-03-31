document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registration-form");
    if (!form) {
        return;
    }

    const fullName = document.getElementById("id_full_name");
    const username = document.getElementById("username");
    const email = document.getElementById("email");
    const phone = document.getElementById("id_phone_num");
    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm-password");

    fullName?.addEventListener("blur", () => validateFullName(fullName, "full_name_error"));
    username?.addEventListener("blur", () => {
        const isFormatValid = validateLatinAndNumbers(username, "username_error");
        const isLengthValid = checkUsernameLength(username.value);
        if (isFormatValid && isLengthValid) {
            checkUsernameUnique(username.value);
        }
    });
    email?.addEventListener("blur", () => {
        const isEmailValid = validateEmail(email, "email_error");
        if (isEmailValid) {
            checkEmailUnique(email.value);
        }
    });
    phone?.addEventListener("blur", () => validatePhone(phone, "phone_num_error"));
    password?.addEventListener("blur", validatePasswords);
    confirmPassword?.addEventListener("blur", validatePasswords);

    form.addEventListener("submit", (event) => {
        const valid =
            validateFullName(fullName, "full_name_error") &
            validateLatinAndNumbers(username, "username_error") &
            checkUsernameLength(username?.value || "") &
            validateEmail(email, "email_error") &
            validatePhone(phone, "phone_num_error") &
            validatePasswords();

        if (!valid) {
            event.preventDefault();
        }
    });
});

function validateFullName(input, errorId) {
    const value = input?.value.trim() || "";
    const parts = value.split(/\s+/).filter(Boolean);

    if (value && !/^[А-Яа-яЁё\s]+$/.test(value)) {
        showError(errorId, "Допустимы только кириллица и пробелы.");
        input?.classList.add("error");
        return false;
    }

    if (value && parts.length < 2) {
        showError(errorId, "Введите минимум фамилию и имя.");
        input?.classList.add("error");
        return false;
    }

    if (value && parts.length > 3) {
        showError(errorId, "Укажите не более трёх слов: фамилия, имя и отчество.");
        input?.classList.add("error");
        return false;
    }

    clearError(errorId);
    input?.classList.remove("error");
    return true;
}

function validateLatinAndNumbers(input, errorId) {
    const value = input?.value || "";
    if (value && !/^[a-zA-Z0-9]+$/.test(value)) {
        showError(errorId, "Логин должен содержать только латиницу и цифры.");
        input?.classList.add("error");
        return false;
    }

    clearError(errorId);
    input?.classList.remove("error");
    return true;
}

function validateEmail(input, errorId) {
    const value = input?.value || "";
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (value && !emailRegex.test(value)) {
        showError(errorId, "Введите корректный email.");
        input?.classList.add("error");
        return false;
    }

    clearError(errorId);
    input?.classList.remove("error");
    return true;
}

function validatePhone(input, errorId) {
    const value = input?.value || "";
    if (value && !/^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/.test(value)) {
        showError(errorId, "Введите номер в формате 8(XXX)XXX-XX-XX.");
        input?.classList.add("error");
        return false;
    }

    clearError(errorId);
    input?.classList.remove("error");
    return true;
}

function validatePasswords() {
    const password1 = document.getElementById("password")?.value || "";
    const password2 = document.getElementById("confirm-password")?.value || "";
    const input = document.getElementById("confirm-password");

    if (password1 && password2 && password1 !== password2) {
        showError("password2_error", "Пароли не совпадают.");
        input?.classList.add("error");
        return false;
    }

    clearError("password2_error");
    input?.classList.remove("error");
    return true;
}

function checkUsernameLength(username) {
    if (username && username.length < 6) {
        showError("username_error", "Логин должен быть не короче 6 символов.");
        document.getElementById("username")?.classList.add("error");
        return false;
    }

    clearError("username_error");
    document.getElementById("username")?.classList.remove("error");
    return true;
}

function checkUsernameUnique(username) {
    if (!username) {
        return;
    }

    fetch(`../check-username/?username=${encodeURIComponent(username)}`)
        .then((response) => response.json())
        .then((data) => {
            if (!data.available) {
                showError("username_error", "Этот логин уже занят.");
                document.getElementById("username")?.classList.add("error");
            }
        })
        .catch(() => {});
}

function checkEmailUnique(email) {
    if (!email) {
        return;
    }

    fetch(`../check-email/?email=${encodeURIComponent(email)}`)
        .then((response) => response.json())
        .then((data) => {
            if (!data.available) {
                showError("email_error", "Этот email уже используется.");
                document.getElementById("email")?.classList.add("error");
            }
        })
        .catch(() => {});
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (!element) {
        return;
    }
    element.textContent = message;
    element.style.display = "block";
}

function clearError(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        return;
    }
    element.textContent = "";
    element.style.display = "none";
}
