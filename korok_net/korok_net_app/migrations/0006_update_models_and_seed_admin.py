from django.contrib.auth.hashers import make_password
from django.db import migrations, models
from django.utils import timezone


def forwards_data_fix(apps, schema_editor):
    Applications = apps.get_model("korok_net_app", "Applications")
    Reviews = apps.get_model("korok_net_app", "Reviews")
    User = apps.get_model("auth", "User")

    course_map = {
        "Основы алгоритмизации и программирования": "algorithms",
        "Основы веб-дизайна": "web_design",
        "Основы проектирования баз данных": "databases",
    }
    payment_map = {
        "Наличными": "cash",
        "По номеру телефона": "phone_transfer",
    }

    for application in Applications.objects.all():
        application.title = course_map.get(application.title, application.title)
        application.payment_method = payment_map.get(
            application.payment_method, application.payment_method
        )
        application.save(update_fields=["title", "payment_method"])

    for review in Reviews.objects.filter(created_at__isnull=True):
        review.created_at = timezone.now()
        review.save(update_fields=["created_at"])

    admin_user, created = User.objects.get_or_create(
        username="Admin",
        defaults={
            "email": "admin@koroknet.local",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
            "password": make_password("KorokNET"),
        },
    )
    if not created:
        admin_user.email = "admin@koroknet.local"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.password = make_password("KorokNET")
        admin_user.save(
            update_fields=["email", "is_staff", "is_superuser", "is_active", "password"]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("korok_net_app", "0005_alter_reviews_mark"),
    ]

    operations = [
        migrations.AlterField(
            model_name="applications",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("cash", "Наличными"),
                    ("phone_transfer", "Переводом по номеру телефона"),
                ],
                max_length=20,
                verbose_name="Способ оплаты",
            ),
        ),
        migrations.AlterField(
            model_name="applications",
            name="title",
            field=models.CharField(
                choices=[
                    ("algorithms", "Основы алгоритмизации и программирования"),
                    ("web_design", "Основы веб-дизайна"),
                    ("databases", "Основы проектирования баз данных"),
                ],
                max_length=32,
                verbose_name="Наименование курса",
            ),
        ),
        migrations.AlterField(
            model_name="reviews",
            name="application",
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                related_name="reviews",
                to="korok_net_app.applications",
                verbose_name="Заявка",
            ),
        ),
        migrations.AddField(
            model_name="reviews",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=timezone.now,
                verbose_name="Дата публикации",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="userinformation",
            name="patronymic",
            field=models.CharField(blank=True, max_length=100, verbose_name="Отчество"),
        ),
        migrations.AlterField(
            model_name="userinformation",
            name="phone_num",
            field=models.CharField(max_length=16, unique=True, verbose_name="Номер телефона"),
        ),
        migrations.RunPython(forwards_data_fix, migrations.RunPython.noop),
    ]
