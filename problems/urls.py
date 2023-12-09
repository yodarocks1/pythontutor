from django.urls import include, path

from . import views

def slug_path(url, *args, **kwargs):
    return (
        path('<slug:slug>-<int:pk>' + url, *args, **kwargs),
        path('<int:pk>' + url, *args, kwargs={"slug": None}, **kwargs),
        #path('<slug:slug>' + url, *args, kwargs={"pk": None}, **kwargs),
    )

urlpatterns = [
    path('', views.list, name="list"),
    *slug_path('', views.view, name="view"),
    *slug_path('/hint', views.hint, name="hint"),
    *slug_path('/test', views.test, name="test"),
    *slug_path('/save', views.on_save, name="save"),
    *slug_path('/submit', views.submit, name="submit"),
    path('run', views.run, name="run"),
]

