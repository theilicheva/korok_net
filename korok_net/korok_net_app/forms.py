import re
from datetime import date
from html import unescape

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.html import strip_tags

from .models import (
    ApplicationStatusChoices,
    Applications,
    CourseChoices,
    PaymentMethodChoices,
    Reviews,
    UserInformation,
)


USERNAME_REGEX = re.compile(r"^[A-Za-z0-9]{6,}$")
FULL_NAME_REGEX = re.compile(r"^[А-Яа-яЁё\s]+$")
PHONE_REGEX = re.compile(r"^8\(\d{3}\)\d{3}-\d{2}-\d{2}$")
HTML_TAG_REGEX = re.compile(r"<[^>]+>")
SCRIPT_REGEX = re.compile(r"(?is)<\s*script\b|javascript:")


def validate_no_markup(value, field_label):
    if not isinstance(value, str):
        return value

    normalized = unescape(value).strip()
    if (
        SCRIPT_REGEX.search(normalized)
        or HTML_TAG_REGEX.search(normalized)
        or strip_tags(normalized) != normalized
        or "<" in normalized
        or ">" in normalized
    ):
        raise forms.ValidationError(
            f"{field_label} не должно содержать HTML-теги или скрипты."
        )
    return value


class StyledFormMixin:
    default_input_class = "input"

    def apply_base_styles(self):
        for field in self.fields.values():
            current = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{current} {self.default_input_class}".strip()


class RegistrationUserForm(StyledFormMixin, UserCreationForm):
    username = forms.CharField(
        label="Логин",
        min_length=6,
        help_text="Используйте латиницу и цифры, не короче 6 символов.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Например, studio24",
                "autocomplete": "username",
                "id": "username",
            }
        ),
    )
    full_name = forms.CharField(
        label="ФИО",
        help_text="Укажите фамилию и имя на кириллице. Отчество можно добавить третьим словом.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Петрова Анна Сергеевна",
                "autocomplete": "name",
                "id": "id_full_name",
            }
        ),
    )
    phone_num = forms.CharField(
        label="Телефон",
        help_text="Формат номера: 8(XXX)XXX-XX-XX",
        widget=forms.TextInput(
            attrs={
                "placeholder": "8(912)345-67-89",
                "id": "id_phone_num",
                "inputmode": "numeric",
            }
        ),
    )
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "hello@portfolio.ru",
                "autocomplete": "email",
                "id": "email",
            }
        ),
    )
    password1 = forms.CharField(
        label="Пароль",
        min_length=8,
        help_text="Минимум 8 символов.",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Придумайте надежный пароль",
                "autocomplete": "new-password",
                "id": "password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Введите пароль повторно",
                "autocomplete": "new-password",
                "id": "confirm-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "full_name",
            "phone_num",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_base_styles()

    def clean_username(self):
        username = self.cleaned_data["username"]
        if not USERNAME_REGEX.fullmatch(username):
            raise forms.ValidationError(
                "Логин должен содержать только латиницу и цифры, минимум 6 символов."
            )
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Этот логин уже занят.")
        return username

    def clean_full_name(self):
        full_name = validate_no_markup(self.cleaned_data["full_name"], "ФИО")
        full_name = " ".join(full_name.split())
        if not FULL_NAME_REGEX.fullmatch(full_name):
            raise forms.ValidationError("ФИО должно содержать только кириллицу и пробелы.")

        parts = full_name.split(" ")
        if len(parts) < 2 or len(parts) > 3:
            raise forms.ValidationError(
                "Введите фамилию и имя. Отчество можно указать третьим словом."
            )

        self.cleaned_data["surname"] = parts[0]
        self.cleaned_data["name"] = parts[1]
        self.cleaned_data["patronymic"] = parts[2] if len(parts) == 3 else ""
        return full_name

    def clean_phone_num(self):
        phone_num = self.cleaned_data["phone_num"]
        if not PHONE_REGEX.fullmatch(phone_num):
            raise forms.ValidationError("Телефон должен быть в формате 8(XXX)XXX-XX-XX.")
        if UserInformation.objects.filter(phone_num=phone_num).exists():
            raise forms.ValidationError("Этот номер телефона уже используется.")
        return phone_num

    def clean_email(self):
        email = validate_no_markup(
            self.cleaned_data["email"], "Электронная почта"
        ).lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Этот email уже используется.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            UserInformation.objects.create(
                user=user,
                surname=self.cleaned_data["surname"],
                name=self.cleaned_data["name"],
                patronymic=self.cleaned_data["patronymic"],
                phone_num=self.cleaned_data["phone_num"],
            )
        return user


class AuthorizationUserForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(
            attrs={"placeholder": "Ваш логин в системе", "autocomplete": "username"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={"placeholder": "Текущий пароль", "autocomplete": "current-password"}
        ),
    )

    error_messages = {
        "invalid_login": "Неверный логин или пароль.",
        "inactive": "Эта учетная запись отключена.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_base_styles()


class ApplicationForm(StyledFormMixin, forms.ModelForm):
    title = forms.ChoiceField(
        label="Направление",
        choices=CourseChoices.choices,
        widget=forms.Select(),
    )
    start_at = forms.DateField(
        label="Старт потока",
        input_formats=["%Y-%m-%d", "%d.%m.%Y"],
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Выберите удобную дату запуска обучения.",
        error_messages={"invalid": "Введите дату в формате ДД.ММ.ГГГГ."},
    )
    payment_method = forms.ChoiceField(
        label="Формат оплаты",
        choices=PaymentMethodChoices.choices,
        widget=forms.Select(),
    )

    class Meta:
        model = Applications
        fields = ["title", "start_at", "payment_method"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_base_styles()

    def clean_start_at(self):
        start_at = self.cleaned_data["start_at"]
        if start_at < date.today():
            raise forms.ValidationError("Дата начала обучения не может быть в прошлом.")
        return start_at


class ReviewForm(StyledFormMixin, forms.ModelForm):
    application = forms.CharField(required=False, widget=forms.HiddenInput())
    mark = forms.ChoiceField(
        label="Оценка",
        choices=Reviews._meta.get_field("mark").choices,
        widget=forms.Select(),
    )
    text = forms.CharField(
        label="Отзыв",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Что особенно понравилось в программе и подаче материала?",
            }
        ),
        min_length=10,
    )

    class Meta:
        model = Reviews
        fields = ["mark", "text"]

    def __init__(self, *args, application=None, **kwargs):
        self.application = application
        super().__init__(*args, **kwargs)
        if self.application is not None:
            self.instance.application = self.application
        self.apply_base_styles()

    def clean(self):
        cleaned_data = super().clean()
        if self.application is None:
            raise forms.ValidationError("Не удалось определить заявку для отзыва.")
        if self.application.status != ApplicationStatusChoices.FINISHED:
            raise forms.ValidationError(
                "Оставить отзыв можно только после завершения обучения."
            )
        if Reviews.objects.filter(application=self.application).exists():
            raise forms.ValidationError("Для этой заявки отзыв уже оставлен.")
        if "text" in cleaned_data:
            cleaned_data["text"] = validate_no_markup(cleaned_data["text"], "Отзыв")
        return cleaned_data

    def save(self, commit=True):
        review = super().save(commit=False)
        review.application = self.application
        if commit:
            review.save()
        return review


class AdminApplicationFilterForm(StyledFormMixin, forms.Form):
    q = forms.CharField(
        label="Поиск",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Курс, пользователь или телефон"}),
    )
    status = forms.ChoiceField(
        label="Статус",
        required=False,
        choices=[("", "Все статусы"), *ApplicationStatusChoices.choices],
        widget=forms.Select(),
    )
    course = forms.ChoiceField(
        label="Курс",
        required=False,
        choices=[("", "Все курсы"), *CourseChoices.choices],
        widget=forms.Select(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_base_styles()

    def clean_q(self):
        q = self.cleaned_data["q"]
        return validate_no_markup(q, "Поиск")


class AdminStatusUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Applications
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "input input--compact"})}


class AdminDirectLoginForm(StyledFormMixin, forms.Form):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={"placeholder": "Служебный логин"}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Служебный пароль"}),
    )

    error_messages = {"invalid_login": "Неверный логин или пароль администратора."}

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        self.apply_base_styles()

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        if username and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None or not self.user_cache.is_staff:
                raise forms.ValidationError(self.error_messages["invalid_login"])
        return cleaned_data

    def get_user(self):
        return self.user_cache
