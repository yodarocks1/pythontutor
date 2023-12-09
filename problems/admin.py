from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db.models import ManyToManyField
from django.urls import reverse

from . import models
from . import widgets

class ProblemTestInline(admin.TabularInline):
    model = models.ProblemTest
    fields = ["view_name", "run_on_save", "run_on_test", "run_on_hint", "run_on_submit", "prerun", "priority"]
    readonly_fields = ["view_name"]
    extra = 0
    show_change_link = True
    can_delete = False
    ordering = ("prerun", "-priority",)

    def view_name(self, obj):
        if obj.name:
            return obj.name
        else:
            return str(obj)

class ProblemAdmin(admin.ModelAdmin):
    inlines = [
        ProblemTestInline,
    ]
    autocomplete_fields = ["languages"]
    list_display = ["name", "languages_html"]

    def view_on_site(self, obj):
        url = reverse("view", kwargs={"pk": obj.pk})
        return url

class ProblemTestAdmin(admin.ModelAdmin):
    list_display = ["problem", "name", "run_on_save", "run_on_test", "run_on_hint", "run_on_submit", "priority"]
    list_filter = ["problem", "run_on_save", "run_on_test", "run_on_hint", "run_on_submit"]
    list_display_links = ["problem", "name"]

class LegalLanguageAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name", "code", "runnable"]
    list_editable = ["runnable"]

admin.site.register(models.Problem, ProblemAdmin)
admin.site.register(models.ProblemTest, ProblemTestAdmin)
admin.site.register(models.LegalLanguage, LegalLanguageAdmin)

