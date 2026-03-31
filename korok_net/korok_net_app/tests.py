from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ApplicationForm, RegistrationUserForm, ReviewForm
from .models import (
    ApplicationStatusChoices,
    Applications,
    PaymentMethodChoices,
    UserInformation,
)


class RegistrationUserFormTests(TestCase):
    def test_registration_rejects_invalid_phone(self):
        form = RegistrationUserForm(
            data={
                "username": "student01",
                "full_name": "Иванов Иван Иванович",
                "phone_num": "+79991234567",
                "email": "student@example.ru",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("phone_num", form.errors)

    def test_registration_accepts_valid_payload(self):
        form = RegistrationUserForm(
            data={
                "username": "student01",
                "full_name": "Иванов Иван Иванович",
                "phone_num": "8(999)123-45-67",
                "email": "student@example.ru",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(UserInformation.objects.filter(user=user).exists())

    def test_registration_rejects_html_in_full_name(self):
        form = RegistrationUserForm(
            data={
                "username": "student02",
                "full_name": "<b>Иванов Иван</b>",
                "phone_num": "8(999)123-45-68",
                "email": "student2@example.ru",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)


class ApplicationFormTests(TestCase):
    def test_application_date_cannot_be_in_past(self):
        yesterday = (timezone.localdate() - timedelta(days=1)).strftime("%d.%m.%Y")
        form = ApplicationForm(
            data={
                "title": "algorithms",
                "start_at": yesterday,
                "payment_method": PaymentMethodChoices.CASH,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("start_at", form.errors)


class ReviewFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student01", password="StrongPass123")
        self.user_info = UserInformation.objects.create(
            user=self.user,
            surname="Иванов",
            name="Иван",
            patronymic="Иванович",
            phone_num="8(999)123-45-67",
        )

    def test_review_available_only_for_finished_application(self):
        application = Applications.objects.create(
            author=self.user_info,
            title="algorithms",
            start_at=timezone.localdate() + timedelta(days=7),
            status=ApplicationStatusChoices.NEW,
            payment_method=PaymentMethodChoices.CASH,
        )

        form = ReviewForm(
            data={"mark": 5, "text": "Очень полезный курс и понятная подача материала."},
            application=application,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_finished_application_accepts_review(self):
        application = Applications.objects.create(
            author=self.user_info,
            title="web_design",
            start_at=timezone.localdate() + timedelta(days=7),
            status=ApplicationStatusChoices.FINISHED,
            payment_method=PaymentMethodChoices.PHONE_TRANSFER,
        )

        form = ReviewForm(
            data={"mark": 5, "text": "Очень полезный курс и понятная подача материала."},
            application=application,
        )

        self.assertTrue(form.is_valid(), form.errors)
        review = form.save()
        self.assertEqual(review.application, application)

    def test_review_rejects_html(self):
        application = Applications.objects.create(
            author=self.user_info,
            title="databases",
            start_at=timezone.localdate() + timedelta(days=7),
            status=ApplicationStatusChoices.FINISHED,
            payment_method=PaymentMethodChoices.CASH,
        )

        form = ReviewForm(
            data={"mark": 5, "text": "<script>alert('x')</script>Отличный курс"},
            application=application,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class SeoMetaTests(TestCase):
    def test_main_page_contains_meta_tags_and_social_markup(self):
        response = Client().get(reverse("main"))

        self.assertContains(response, 'name="description"', html=False)
        self.assertContains(response, 'name="keywords"', html=False)
        self.assertContains(response, 'property="og:title"', html=False)
        self.assertContains(response, 'name="twitter:card"', html=False)
