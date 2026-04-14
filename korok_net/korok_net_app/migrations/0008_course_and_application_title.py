from django.db import migrations, models


def seed_courses(apps, schema_editor):
    Course = apps.get_model("korok_net_app", "Course")
    defaults = [
        {
            "code": "algorithms",
            "title": "Основы алгоритмизации и программирования",
            "description": "Изучение логики программ, базовых конструкций, алгоритмов и практических принципов разработки.",
            "sort_order": 10,
            "is_active": True,
        },
        {
            "code": "web_design",
            "title": "Основы веб-дизайна",
            "description": "Работа с композицией, интерфейсами, визуальной иерархией и цифровой подачей материалов.",
            "sort_order": 20,
            "is_active": True,
        },
        {
            "code": "databases",
            "title": "Основы проектирования баз данных",
            "description": "Проектирование структур данных, связей между сущностями и надежных схем хранения информации.",
            "sort_order": 30,
            "is_active": True,
        },
    ]

    for item in defaults:
        Course.objects.update_or_create(code=item["code"], defaults=item)


class Migration(migrations.Migration):
    dependencies = [
        (
            "korok_net_app",
            "0007_alter_applications_options_alter_reviews_options_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.SlugField(
                        allow_unicode=True,
                        max_length=64,
                        unique=True,
                        verbose_name="Код курса",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        max_length=180,
                        unique=True,
                        verbose_name="Название курса",
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Описание курса"),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        verbose_name="Доступен для записи",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=100,
                        verbose_name="Порядок вывода",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Дата создания",
                    ),
                ),
            ],
            options={
                "verbose_name": "Курс",
                "verbose_name_plural": "Курсы",
                "db_table": "courses",
                "ordering": ["sort_order", "title"],
            },
        ),
        migrations.AlterField(
            model_name="applications",
            name="title",
            field=models.CharField(
                max_length=64,
                verbose_name="Наименование курса",
            ),
        ),
        migrations.RunPython(seed_courses, migrations.RunPython.noop),
    ]
