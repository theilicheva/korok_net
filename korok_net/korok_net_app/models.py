from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class PaymentMethodChoices(models.TextChoices):
    CASH = ("cash", "Наличными")
    PHONE_TRANSFER = ("phone_transfer", "Переводом по номеру телефона")


class ApplicationStatusChoices(models.TextChoices):
    NEW = ("new", "Новая")
    IN_PROCESS = ("in_process", "Идет обучение")
    FINISHED = ("finished", "Обучение завершено")


class Course(models.Model):
    code = models.SlugField(
        max_length=64,
        unique=True,
        allow_unicode=True,
        verbose_name="Код курса",
    )
    title = models.CharField(
        max_length=180,
        unique=True,
        verbose_name="Название курса",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание курса",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Доступен для записи",
    )
    sort_order = models.PositiveIntegerField(
        default=100,
        verbose_name="Порядок вывода",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        db_table = "courses"
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    @classmethod
    def build_unique_code(cls, title):
        base_code = slugify(title, allow_unicode=True) or "course"
        candidate = base_code[:64]
        suffix = 2

        while cls.objects.filter(code=candidate).exists():
            tail = f"-{suffix}"
            candidate = f"{base_code[: 64 - len(tail)]}{tail}"
            suffix += 1

        return candidate

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.build_unique_code(self.title)
        super().save(*args, **kwargs)


class UserInformation(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="user_info",
        verbose_name="Пользователь",
    )
    phone_num = models.CharField(
        max_length=16,
        unique=True,
        verbose_name="Номер телефона",
    )
    surname = models.CharField(max_length=100, verbose_name="Фамилия")
    name = models.CharField(max_length=100, verbose_name="Имя")
    patronymic = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Отчество",
    )

    class Meta:
        db_table = "user_information"
        verbose_name = "Информация о пользователе"
        verbose_name_plural = "Информация о пользователях"
        ordering = ["id"]

    def __str__(self):
        full_name = " ".join(
            part for part in [self.surname, self.name, self.patronymic] if part
        )
        return full_name

    @property
    def short_name(self):
        initials = f"{self.name[:1]}."
        if self.patronymic:
            initials += f" {self.patronymic[:1]}."
        return f"{self.surname} {initials}"


class Applications(models.Model):
    author = models.ForeignKey(
        UserInformation,
        on_delete=models.CASCADE,
        related_name="applications",
        null=True,
        blank=True,
        verbose_name="Автор",
    )
    title = models.CharField(
        max_length=64,
        verbose_name="Наименование курса",
    )
    start_at = models.DateField(verbose_name="Дата начала обучения")
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    status = models.CharField(
        choices=ApplicationStatusChoices.choices,
        default=ApplicationStatusChoices.NEW,
        max_length=20,
        verbose_name="Статус",
    )
    payment_method = models.CharField(
        choices=PaymentMethodChoices.choices,
        max_length=20,
        verbose_name="Способ оплаты",
    )

    class Meta:
        db_table = "applications"
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.display_title} - {self.author}"

    @property
    def display_title(self):
        if hasattr(self, "_display_title_cache"):
            return self._display_title_cache

        course = Course.objects.filter(code=self.title).only("title").first()
        self._display_title_cache = course.title if course else self.title
        return self._display_title_cache

    @property
    def has_review(self):
        try:
            return self.reviews is not None
        except Reviews.DoesNotExist:
            return False


class Reviews(models.Model):
    application = models.OneToOneField(
        Applications,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Заявка",
    )
    mark = models.SmallIntegerField(
        verbose_name="Оценка",
        choices=[
            (1, "Очень плохо"),
            (2, "Плохо"),
            (3, "Удовлетворительно"),
            (4, "Хорошо"),
            (5, "Отлично"),
        ],
    )
    text = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
    )

    class Meta:
        db_table = "reviews"
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

    def clean(self):
        if not self.application_id:
            raise ValidationError("Заявка не указана.")

        if self.application.status != ApplicationStatusChoices.FINISHED:
            raise ValidationError(
                {"application": "Отзыв можно оставить только после завершения обучения."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application} - оценка: {self.mark}"
