from django.contrib import admin

from .models import Applications, Reviews, UserInformation


@admin.register(UserInformation)
class UserInformationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "surname", "name", "patronymic", "phone_num")
    search_fields = ("surname", "name", "patronymic", "phone_num", "user__username")
    list_per_page = 20


@admin.register(Applications)
class ApplicationsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "title",
        "start_at",
        "status",
        "payment_method",
        "created_at",
    )
    list_filter = ("status", "title", "payment_method", "start_at")
    search_fields = (
        "author__surname",
        "author__name",
        "author__phone_num",
        "author__user__username",
    )
    autocomplete_fields = ("author",)
    list_per_page = 20


@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "mark", "created_at")
    list_filter = ("mark", "created_at")
    search_fields = ("application__author__surname", "application__author__user__username", "text")
    list_per_page = 20


admin.site.site_header = "Корочки.есть"
admin.site.site_title = "Корочки.есть"
admin.site.index_title = "Системное администрирование"
