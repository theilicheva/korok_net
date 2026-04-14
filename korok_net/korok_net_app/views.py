from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, ListView, TemplateView

from .forms import (
    AdminApplicationFilterForm,
    AdminCourseForm,
    AdminDirectLoginForm,
    AdminStatusUpdateForm,
    ApplicationForm,
    AuthorizationUserForm,
    RegistrationUserForm,
    ReviewForm,
)
from .models import ApplicationStatusChoices, Applications, Course, Reviews


class CheckUsernameView(View):
    def get(self, request):
        username = request.GET.get("username", "")
        available = not User.objects.filter(username__iexact=username).exists()
        return JsonResponse({"available": available})


class CheckEmailView(View):
    def get(self, request):
        email = request.GET.get("email", "")
        available = not User.objects.filter(email__iexact=email).exists()
        return JsonResponse({"available": available})


class RegistrationView(FormView):
    template_name = "korok_net_app/registration.html"
    form_class = RegistrationUserForm
    success_url = reverse_lazy("main")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("admin_panel" if request.user.is_staff else "main")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Профиль создан. Теперь можно оформить первую заявку.")
        return super().form_valid(form)


class AuthorizationView(FormView):
    template_name = "korok_net_app/authorization.html"
    form_class = AuthorizationUserForm
    success_url = reverse_lazy("main")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("admin_panel" if request.user.is_staff else "main")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        login(self.request, form.get_user())
        messages.success(self.request, "Авторизация прошла успешно.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admin_panel" if self.request.user.is_staff else "main")


class AdminLoginView(FormView):
    template_name = "korok_net_app/admin_login.html"
    form_class = AdminDirectLoginForm
    success_url = reverse_lazy("admin_panel")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect("admin_panel")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        login(self.request, form.get_user())
        messages.success(self.request, "Добро пожаловать в панель администратора.")
        return super().form_valid(form)


def logout_user(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect("main")


class HomeView(TemplateView):
    template_name = "korok_net_app/main.html"

    def get_application_form(self, form=None):
        application_form = form or ApplicationForm()
        if self.request.user.is_authenticated and self.request.user.is_staff:
            for field in application_form.fields.values():
                field.widget.attrs["disabled"] = "disabled"
        return application_form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_courses = Course.objects.filter(is_active=True).order_by("sort_order", "title")
        context["form"] = self.get_application_form(kwargs.get("form"))
        context["course_cards"] = active_courses[:6]
        context["featured_reviews"] = Reviews.objects.select_related(
            "application", "application__author", "application__author__user"
        ).filter(application__status=ApplicationStatusChoices.FINISHED).order_by(
            "-created_at"
        )[:3]
        context["hero_stats"] = {
            "courses": active_courses.count(),
            "applications": Applications.objects.count(),
            "completed": Applications.objects.filter(
                status=ApplicationStatusChoices.FINISHED
            ).count(),
        }
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Сначала войдите в аккаунт или зарегистрируйтесь.")
            return redirect("authorization")

        if request.user.is_staff:
            messages.info(
                request,
                "Для работы с заявками используйте панель администратора.",
            )
            return redirect("admin_panel")

        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.author = request.user.user_info
            application.save()
            messages.success(
                request,
                "Заявка отправлена администратору. Статус можно отслеживать в личном кабинете.",
            )
            return redirect("user_applications")

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class ApplicationsView(LoginRequiredMixin, ListView):
    model = Applications
    paginate_by = 6
    template_name = "korok_net_app/user_applications.html"
    context_object_name = "applications"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return redirect("admin_panel")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Applications.objects.filter(author=self.request.user.user_info)
            .select_related("author", "author__user", "reviews")
        )

    def post(self, request, *args, **kwargs):
        application = get_object_or_404(
            Applications.objects.select_related("author"),
            pk=request.POST.get("application_id"),
            author=request.user.user_info,
        )
        form = ReviewForm(request.POST, application=application)
        if form.is_valid():
            form.save()
            messages.success(request, "Спасибо! Ваш отзыв сохранен.")
            return redirect("user_applications")

        self.object_list = self.get_queryset()
        context = self.get_context_data(review_form=form, review_target=application.id)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["review_form"] = kwargs.get("review_form") or ReviewForm()
        context["review_target"] = kwargs.get("review_target")
        return context


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy("admin_login")

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Доступ к панели администратора ограничен.")
            return redirect("main")
        return redirect(self.login_url)


class AdminPanelView(AdminRequiredMixin, ListView):
    model = Applications
    paginate_by = 4
    template_name = "korok_net_app/admin_panel.html"
    context_object_name = "applications"

    def get_filter_form(self):
        return AdminApplicationFilterForm(self.request.GET or None)

    def get_course_form(self):
        return getattr(self, "course_form", AdminCourseForm())

    def apply_application_filters(self, queryset):
        if self.filter_form.is_valid():
            q = self.filter_form.cleaned_data.get("q")
            status = self.filter_form.cleaned_data.get("status")
            course = self.filter_form.cleaned_data.get("course")

            if q:
                matched_course_codes = list(
                    Course.objects.filter(title__icontains=q).values_list("code", flat=True)
                )
                queryset = queryset.filter(
                    Q(author__surname__icontains=q)
                    | Q(author__name__icontains=q)
                    | Q(author__patronymic__icontains=q)
                    | Q(author__phone_num__icontains=q)
                    | Q(author__user__username__icontains=q)
                    | Q(title__in=matched_course_codes)
                )
            if status:
                queryset = queryset.filter(status=status)
            if course:
                queryset = queryset.filter(title=course)
        return queryset

    def get_queryset(self):
        queryset = (
            Applications.objects.select_related("author", "author__user", "reviews")
            .order_by("-created_at")
        )
        self.filter_form = self.get_filter_form()
        return self.apply_application_filters(queryset)

    def render_with_errors(self):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "create_course":
            self.course_form = AdminCourseForm(request.POST)
            if self.course_form.is_valid():
                course = self.course_form.save()
                messages.success(request, f"Курс «{course.title}» добавлен и доступен пользователям.")
                return redirect("admin_panel")
            messages.error(request, "Не удалось добавить курс. Проверьте заполнение формы.")
            return self.render_with_errors()

        if action == "delete_review":
            review = get_object_or_404(Reviews, pk=request.POST.get("review_id"))
            course_title = review.application.display_title
            review.delete()
            messages.success(request, f"Отзыв по курсу «{course_title}» удален.")
            return redirect("admin_panel")

        application = get_object_or_404(Applications, pk=request.POST.get("application_id"))
        form = AdminStatusUpdateForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Статус заявки для курса «{application.display_title}» обновлен.",
            )
        else:
            messages.error(request, "Не удалось обновить статус заявки.")
        return redirect("admin_panel")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Applications.objects.all()
        course_map = Course.objects.in_bulk(field_name="code")
        context["filter_form"] = getattr(self, "filter_form", self.get_filter_form())
        context["course_form"] = self.get_course_form()
        context["status_form_choices"] = ApplicationStatusChoices.choices
        params = self.request.GET.copy()
        params.pop("page", None)
        context["filter_query"] = params.urlencode()
        context["dashboard"] = {
            "total": queryset.count(),
            "new": queryset.filter(status=ApplicationStatusChoices.NEW).count(),
            "in_process": queryset.filter(
                status=ApplicationStatusChoices.IN_PROCESS
            ).count(),
            "finished": queryset.filter(status=ApplicationStatusChoices.FINISHED).count(),
        }
        context["popular_courses"] = [
            {
                "title": course_map[item["title"]].title
                if item["title"] in course_map
                else item["title"],
                "total": item["total"],
            }
            for item in queryset.values("title").annotate(total=Count("id")).order_by(
                "-total", "title"
            )
        ]
        context["courses_catalog"] = Course.objects.order_by("sort_order", "title")
        return context
