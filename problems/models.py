import json_fix # `pip install json-fix`
 # Allows classes to implement a __json__ method readable by the json library

from enum import Enum

from django import forms
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from django.contrib.auth.models import User
from .widgets import CodeField, MultiCodeField

RESPONSE_TONES = [
    "Professional",
    "Helpful",
    "Friendly",
    "Direct",
    "Academic",
]

class LegalLanguage(models.Model):
    name = models.CharField(max_length=24)
    code = models.CharField(max_length=24, unique=True)
    runnable = models.BooleanField()
    
    def __str__(self):
        return self.name
    def __json__(self):
        return {"name": self.name, "code": self.code, "runnable": self.runnable}
   
    def html(self, link=False):
        if link:
            return format_html("<a href='{}'>{}</a>", self.get_admin_link(), self.html(link=False))
        else:
            return format_html("<em>{}</em>", self.name)

    def get_admin_link(self):
        info = (self._meta.app_label, self._meta.model_name)
        return reverse('admin:%s_%s_change' % info, args=(self.pk,))

    class Meta:
        verbose_name="language"

class Problem(models.Model):
    name = models.CharField(max_length=64)
    languages = models.ManyToManyField(LegalLanguage)
    response_tone = models.CharField(max_length=12, choices=zip(RESPONSE_TONES, RESPONSE_TONES))
    design_requirements = CodeField(tab_name="design_requirements.md", \
            languages=["markdown"], use_test=True)

    starter_code = MultiCodeField(default=dict, use_test=True)
    allow_new_tabs = models.BooleanField(default=True)

    # TODO: Add Knowledge Components
    #           Include explanation hints (ChatGPT?)

    def languages_html(self):
        s = []
        for language in self.languages.all():
            s.append(language.html(link=True))
        return mark_safe(", ".join(s))
    languages_html.short_description = "languages"

    def slug(self):
        return slugify(self.name)

    def get_absolute_url(self):
        return reverse('view', kwargs={'slug': self.slug(), 'pk': self.pk})

    def __str__(self):
        return self.name

class ProblemTest(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="tests")
    name = models.CharField(max_length=32, blank=True)

    run_on_save = models.BooleanField()
    run_on_test = models.BooleanField()
    run_on_hint = models.BooleanField()
    run_on_submit = models.BooleanField()

    prerun = models.BooleanField("runtime", choices=[(True, "Before code is run"), (False, "After code is run")], help_text="Tests that operate before the learner's code is run are run first, in order of priority.")

    halt_testing_on_fail = models.BooleanField()
    priority = models.IntegerField(help_text="Higher values run first. Syntax errors occur before run at priority 2000000000. Values must be between -2147483648 to 2147483647.")

    code = CodeField(tab_name="__test__.py", givens="""
class TestFailure:
    def __init__(self, which, description, context):
        self.which = which # Which design requirement the learner failed to meet
        self.description = description # How the learner failed to meet it
        self.context = context # Some data or other information to provide context
    def to_dict(self):
        return {
            "which": self.which,
            "desc": self.description,
            "context": self.context
        }

class Result:
    def __init__(self):
        self.errors = []
        self.decorations = []
        self.markdownDisplay = ""
    def add_error(self, test_failure):
        self.errors.append(test_failure)
    def add_decoration(self, file, selection, effect):
        # For `effect`, see documentation at https://microsoft.github.io/monaco-editor/typedoc/interfaces/editor.IModelDecorationOptions.html
        self.decorations.append((file, selection, effect))
    def set_display(self, display):
        self.markdownDisplay = display
    def to_dict(self):
        return {
            "errors": list(map(TestFailure.to_dict, self.errors)),
            "decorations": self.decorations,
            "markdownDisplay": self.markdownDisplay
        }

# GIVENS:
#         mode : Why the test is being run (One of ["save", "test", "hint", "submit"])
#         main : 
#         code : 
#     language : 
#       active : (Optional)
#    selection : (Optional)
#  POST-RUN TESTS ONLY:
#       module : The python module created by running the user's code
#       output : The print output created by running the user's code

# Most normal values and attributes starting with an underscore ("_") are off-limits, except for:
#  ("__name__", "__import__")
# If you want to use any others, use getattr(x, "_value")

result = Result()
    """, languages=['python'])

    def full_code(self):
        return ProblemTest._meta.get_field("code").givens.strip() + "\n" + self.code

    def formfield(self, **kwargs):
        defaults = {"widget": CodeWidget("__test__.py", False, False, False)}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def __str__(self):
        if self.name:
            return "Test for " + self.problem.name + ": " + self.name

        cases = []
        if self.run_on_save:
            cases.append("Save")
        if self.run_on_test:
            cases.append("Test")
        if self.run_on_hint:
            cases.append("Hint")
        if self.run_on_submit:
            cases.append("Submit")

        if len(cases) == 0:
            return "Latent test for " + self.problem.name
        else:
            return "Test for " + self.problem.name + " on " + ", ".join(cases)

# TODO: Future work
#class ProblemState(models.Model):
#    student = models.ForeignKey(User, on_delete=models.CASCADE)
#    code = MultiCodeField()
#    test_results = models.JSONField()
    

