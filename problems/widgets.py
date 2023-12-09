import json

from django import forms
from django.db import models
from django.core.exceptions import ValidationError

def _get_language(code):
    if "LegalLanguage" not in globals():
        from .models import LegalLanguage
    if code is None:
        return LegalLanguage.objects.in_bulk()
    return LegalLanguage.objects.get(code=code)

class CodeField(models.TextField):
    def __init__(self, *args, tab_name="__main__.py", languages=None, givens=None, use_hints=False, \
                use_submit=False, use_save=False, use_test=False, use_main=False, **kwargs):
        self.tab_name = tab_name
        self.languages = languages
        self.givens = givens
        self.use_hints = use_hints
        self.use_submit = use_submit
        self.use_save = use_save
        self.use_test = use_test
        self.use_main = use_main
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs["widget"] = CodeWidget(
            self.tab_name,
            givens=self.givens,
            use_hints=self.use_hints,
            use_submit=self.use_submit,
            use_save=self.use_save,
            use_test=self.use_test,
            use_main=self.use_main,
            languages=list(map(_get_language, self.languages)) if self.languages else None,
        )
        return super().formfield(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.tab_name != "__main__.py":
            kwargs["tab_name"] = self.tab_name
        if self.languages is not None:
            kwargs["languages"] = self.languages
        if self.givens is not None:
            kwargs["givens"] = self.givens
        return name, path, args, kwargs

class CodeWidget(forms.widgets.Widget):
    template_name = 'widgets/code_widget.html'
    def __init__(self, tab_name, *args, givens=None, \
                 use_hints=True, use_submit=True, use_save=True, use_test=True, use_main=True, \
                 html_id=None, languages=None, **kwargs):
        self.givens = givens
        self.use_hints = use_hints
        self.use_submit = use_submit
        self.use_save = use_save
        self.use_test = use_test
        self.use_main = use_main
        self.html_id = html_id
        self.tab_name = tab_name
        self.languages = languages
        self.allow_new_tabs = False
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        s = value or ""
        context["starter_code"] = {self.tab_name: s}
        context["allow_new_tabs"] = bool(self.allow_new_tabs)
        context["use_hints"] = bool(self.use_hints)
        context["use_submit"] = bool(self.use_submit)
        context["use_save"] = bool(self.use_save)
        context["use_test"] = bool(self.use_test)
        use_main = False
        if self.languages is None:
            context["all_languages"] = _get_language(None)
        elif self.use_main:
            for language in self.languages:
                if language.runnable:
                    use_main = True
                    break
        context["use_main"] = use_main
        if self.html_id is None:
            context["html_id"] = name + "-editor"
        else:
            context["html_id"] = self.html_id
        context["languages"] = self.languages
        context["link_input"] = [name, self.tab_name]
        context["givens"] = self.givens
        return context

    def use_required_attribute(self, initial):
        return False


class MultiCodeField(models.JSONField):
    def __init__(self, *args, languages=None, givens=None, use_hints=False, \
                use_submit=False, use_save=False, use_test=False, use_main=False, **kwargs):
        self.languages = languages
        self.givens = givens
        self.use_hints = use_hints
        self.use_submit = use_submit
        self.use_save = use_save
        self.use_test = use_test
        self.use_main = use_main
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs["widget"] = MultiCodeWidget(
            use_hints=self.use_hints,
            use_submit=self.use_submit,
            use_save=self.use_save,
            use_test=self.use_test,
            use_main=self.use_main,
            givens=self.givens,
            languages=list(map(_get_language, self.languages)) if self.languages else None,
        )
        return super().formfield(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.languages is not None:
            kwargs["languages"] = self.languages
        if self.givens is not None:
            kwargs["givens"] = self.givens
        return name, path, args, kwargs

class MultiCodeWidget(forms.widgets.Widget):
    template_name = 'widgets/code_widget.html'
    def __init__(self, *args, givens=None, \
                 use_hints=True, use_submit=True, use_save=True, use_test=True, use_main=True, \
                 html_id=None, languages=None, **kwargs):
        self.givens = givens
        self.use_hints = use_hints
        self.use_submit = use_submit
        self.use_save = use_save
        self.use_test = use_test
        self.use_main = use_main
        self.html_id = html_id
        self.languages = languages
        self.allow_new_tabs = True
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["starter_code"] = json.loads(value or "{}")
        context["allow_new_tabs"] = bool(self.allow_new_tabs)
        context["use_hints"] = bool(self.use_hints)
        context["use_submit"] = bool(self.use_submit)
        context["use_save"] = bool(self.use_save)
        context["use_test"] = bool(self.use_test)
        use_main = False
        if self.languages is None:
            context["all_languages"] = _get_language(None)
        elif self.use_main:
            for language in self.languages:
                if language.runnable:
                    use_main = True
                    break
        context["use_main"] = use_main
        if self.html_id is None:
            context["html_id"] = name + "-editor"
        else:
            context["html_id"] = self.html_id
        context["languages"] = self.languages
        context["link_input"] = [name]
        context["givens"] = self.givens
        return context

    def use_required_attribute(self, initial):
        return False

