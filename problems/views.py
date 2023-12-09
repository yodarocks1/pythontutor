import requests
import functools

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse

from .models import Problem
from .runcode import run_code, test_code

def _read_zzzcode_response(endpoint, data):
    r = requests.post(endpoint, json=data, stream=True)
    messageId = None
    redirect = False
    chunked = []
    current = ""
    for chunk in r.iter_content(8192):
        current += chunk.decode('utf-8')
        if "data: " in current:
            split = current.split("data: ")
            if len(split[0].strip()) != 0:
                chunked.append(split[0])
            current = split[1]
    chunked.append(current)
 
    s = ""
    for chunk in chunked:
        chunk = chunk.strip()[1:-1]
        if chunk == "zzz_completed_zzz":
            break;
        elif chunk.startswith("zzzredirectmessageidzzz:"):
            messageId = chunk.replace("zzzredirectmessageidzzz:", "").strip()
            redirect = True
        elif chunk.startswith("zzzmessageidzzz:"):
            messageId = chunk.replace("zzzmessageidzzz:", "").strip()
        else:
            s += chunk

    if redirect:
        s = _read_zzzcode_response(endpoint, {"id": messageId, "hasBlocker": True})
    return s.replace("zzznewlinezzz", "\n")

def list(request):
    problems = Problem.objects.all()
    return render(request, "problems/list.html", {
        "problems": problems,
    })


def problem_view(func):
    @functools.wraps(func)
    def wrapped_view(request, slug, pk):
        problem = get_object_or_404(Problem, pk=pk)
        expected_slug = problem.slug()
        if slug is None or slug != expected_slug:
            result = redirect(request.resolver_match.view_name, slug=expected_slug, pk=pk)
            result.status_code = 307
            return result
        return func(request, problem)
    return wrapped_view

@problem_view
def view(request, problem):
    return render(request, "problems/view.html", {
        "problem": problem,
    })

@problem_view
def hint(request, problem):
    return test_code(request, "hint", problem.tests.filter(run_on_hint=True))

@problem_view
def test(request, problem):
    return test_code(request, "test", problem.tests.filter(run_on_test=True))

@problem_view
def submit(request, problem):
    return test_code(request, "submit", problem.tests.filter(run_on_submit=True))

@problem_view
def on_save(request, problem):
    return test_code(request, "save", problem.tests.filter(run_on_submit=True))

def run(request):
    return run_code(request, None)

#def submit(request, pk):
#    problem = get_object_or_404(Problem, pk=pk)
#    return run_code(request, problem.test_code)

