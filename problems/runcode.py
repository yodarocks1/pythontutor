import json
import types
import traceback
import linecache
import re
import sys

import RestrictedPython
from RestrictedPython.Guards import guarded_iter_unpack_sequence, guarded_unpack_sequence

from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from .models import Problem

_ALLOWED_SPECIAL_NAMES = ["__name__", "__print_result__", "__import__"]
_ALLOWED_SPECIAL_ATTRIBUTES = ["__print_result__"]
class OwnRestrictingNodeTransformer(RestrictedPython.RestrictingNodeTransformer):
    def check_name(self, node, name, allow_magic_methods=False):
        if name in _ALLOWED_SPECIAL_NAMES:
            return
        else:
            return super().check_name(node, name, allow_magic_methods=allow_magic_methods)
    def visit_Attribute(self, node):
        node = super().visit_Attribute(node)
        if len(self.errors) > 0 and self.errors[-1].endswith("is an invalid attribute name because it starts with \"_\"."):
            if self.errors[-1].split("\"")[1] in _ALLOWED_SPECIAL_ATTRIBUTES:
                del self.errors[-1]
        return node
_POLICY = OwnRestrictingNodeTransformer

_SAFE_MODULES = frozenset(("math","random","re"))
def _create_safe_import(code, relative_import):
    def _safe_import(name, *args, **kwargs):
        if name + ".py" in code:
            m = relative_import(name + ".py")
            return m
        elif name not in _SAFE_MODULES:
            raise SyntaxError(f"Invalid module name: {name!r}")
        return __import__(name, *args, **kwargs)
    return _safe_import

class Loader:
    def __init__(self, code):
        self.code = code
    def get_source(self, name):
        return self.code

_IMPORT_REGEX = r"^(?P<start>\s*)import \.(?P<module>\w+)[ \t]*$"
_IMPORT_SUB_STRING = r"\g<start>\g<module> = __import__('.\g<module>')"
_IMPORT_ADD_PRINT = "\n" + r"\g<start>print(\g<module>.__print_result__, end='')"
_ADD_PRINT = "\n\nprint(end='')\ntry: __print_result__ += printed\nexcept NameError: __print_result__ = printed"
def _compile_and_import(code, name, my_globals, policy=_POLICY, add_print=True):
    sub_string = _IMPORT_SUB_STRING
    if add_print:
        sub_string += _IMPORT_ADD_PRINT
    code = re.sub(_IMPORT_REGEX, sub_string, code, flags=re.M)
    if add_print:
        code += _ADD_PRINT
    try:
        byte_code = RestrictedPython.compile_restricted(
            code,
            filename=name,
            mode="exec",
            policy=policy
        )
    except BaseException as e:
        setattr(e, "filename", name)
        raise e
    new_globals = {
        **my_globals,
        "__name__": re.sub(".py$", "", name),
        "__loader__": Loader(code) # Allows exceptions to read the source code
    }
    exec(byte_code, new_globals)
    m = types.ModuleType(name)
    m.__dict__.update(new_globals)
    return m

PATH = list(filter(lambda x: len(x) > 0, sys.path))
def _exception_to_decorations(exception):
    if type(exception) is SyntaxError and type(exception.msg) is tuple:
        for msg in exception.msg:
            m = re.match(r"Line ([0-9]+): (.*)", msg)
            return [[
                exception.filename,
                (int(m.group(1)), 1, int(m.group(1)), -1),
                {
                    "className": "error-underline",
                    "hoverMessage": m.group(2).replace("'", "```"),
                    "overviewRuler": {"color": "darkred", "position": 7},
                }
            ]]
    
    tb = exception.__traceback__
    tb_ = tb
    while tb_.tb_next:
        tb_ = tb_.tb_next
        if "pythontutor/problems/" not in tb_.tb_frame.f_code.co_filename:
            tb = tb_
    fname = tb.tb_frame.f_code.co_filename
    lineno = tb.tb_lineno
    linecache.lazycache(fname, tb.tb_frame.f_globals)
    l = linecache.getline(fname, lineno)

    colno = 1
    end_colno = -1
    include_type = True

    if type(exception) is NameError:
        if hasattr(exception, "name") and exception.name:
            include_type = False
            try:
                colno = l.index(exception.name) + 1
                end_colno = colno + len(exception.name)
            except:
                colno = 1
                end_colno = -1
    elif issubclass(type(exception), LookupError):
        include_type = type(exception) is KeyError
        try:
            colno = l.index("[") + 1
            end_colno = len(l) - 1 - l[::-1].index("]") + 2
            if type(exception) is KeyError:
                if type(exception.args[0]) in (int, str) and str(exception) in l:
                    colno = l.index(str(exception), colno)
                    end_colno = colno + len(str(exception)) + 2
                elif type(exception.args[0]) is str and str(exception).replace("'", "\"") in l:
                    colno = l.index(str(exception).replace("'", "\""), colno)
                    end_colno = colno + len(str(exception)) + 2
        except:
            colno = 1
            end_colno = -1

    #TODO
    elif type(exception) is ImportError:
        pass
    elif type(exception) is TypeError:
        pass
    elif type(exception) is ValueError:
        pass

    return [[
        fname,
        (lineno, colno, lineno, end_colno),
        {
            "className": "error-underline",
            "hoverMessage": (f"{type(exception).__name__}: " if include_type else "") + str(exception),
            "overviewRuler": {"color": "darkred", "position": 7},
            "isWholeLine": (colno == 1 and end_colno == -1),
        }
    ]]

    return []

def _serialize_syntax_error(exception):
    if type(exception.msg) is tuple:
        return list(map(lambda l: l + "\n", exception.msg))
    return _serialize_exception(exception, pretty_syntax_error=False)
def _serialize_exception(exception, pretty_syntax_error=False, hide=True):
    if pretty_syntax_error and type(exception) is SyntaxError:
        return _serialize_syntax_error(exception)

    trace = traceback.format_exception(exception)
    if not hide:
        return trace
    filtered_trace = []
    filtered = 0
    for line in trace:
        if "pythontutor/problems/" in line:
            filtered += 1
            continue
        elif filtered > 0:
            filtered_trace.append(f"  ({filtered} hidden lines)\n")
            filtered = 0
        for path in PATH:
            if "File \"" + path in line:
                filtered_trace.append(line.replace(path, "PYTHONPATH"))
                break
        else:
            filtered_trace.append(line.replace(", in <module>", ""))
    #return trace
    return filtered_trace

def inplace_guard(op, val, expr):
    if op == "+=":
        return val + expr
    elif op == "-=":
        return val - expr
    elif op == "*=":
        return val * expr
    elif op == "/=":
        return val / expr
    elif op == "%=":
        return val % expr
    elif op == "**=":
        return val ** expr
    elif op == "<<=":
        return val << expr
    elif op == ">>=":
        return val >> expr
    elif op == "|=":
        return val | expr
    elif op == "^=":
        return val ^ expr
    elif op == "&=":
        return val & expr
    elif op == "//=":
        return val // expr
    else:
        raise SyntaxError(op)
def create_globals(code, test_mode=False):
    if test_mode:
        base_builtins = {
            **globals()["__builtins__"],
        }
    else:
        base_builtins = {}
    my_globals = {
        "__builtins__": {
            **base_builtins,
            **RestrictedPython.safe_builtins,
            "_print_": RestrictedPython.PrintCollector,
            "_getattr_": getattr,
            "_getiter_": lambda x: x,
            "_getitem_": lambda x, y: x[y],
            "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
            "_unpack_sequence_": guarded_unpack_sequence,
            "_inplacevar_": inplace_guard,
            "_write_": lambda x: x,
            "__metaclass__": type,
        },
    }
    _safe_import = _create_safe_import(code, lambda x: _compile_and_import(code[x], x, my_globals))
    my_globals["__builtins__"]["__import__"] = _safe_import
    my_globals["__import__"] = _safe_import
    return my_globals

def run_code(main, code):
    my_globals = create_globals(code)

    try:
        main_module = _compile_and_import(code[main], "__main__", my_globals)
    except SyntaxError as e:
        return {
            "error_type": SyntaxError,
            "error": e,
        }
    except BaseException as e:
        return {
            "error_type": BaseException,
            "error": e,
        }
    output = main_module.__print_result__
    del main_module.__print_result__

    return {
        "module": main_module,
        "output": output,
    }

def run_test(problem_data, test):
    if test.prerun:
        data = problem_data.prerun_data()
    else:
        data = problem_data.postrun_data()
    my_globals = create_globals(problem_data.code, test_mode=True)

    try:
        test_module = _compile_and_import(test.full_code(), "__test__", {**my_globals, **data})
        result = test_module.result.to_dict()
    except SyntaxError as e:
        return {
            "error_type": "SyntaxError",
            "error": _serialize_exception(e, pretty_syntax_error=True),
            "decorations": _exception_to_decoration(e),
            "context": test.name if test.name else test.pk,
        }
    except BaseException as e:
        return {
            "error_type": type(e).__name__,
            "error": _serialize_exception(e),
            "decorations": _exception_to_decoration(e),
            "context": test.name if test.name else test.pk,
        }
    output = test_module.__print_result__
    del test_module.__print_result__

    return {
        "name": str(test),
        "module": test_module,
        "output": output,
        "result": result
    }

def test_code(request, mode, tests):
    out = parse_request(request, mode)
    if type(out) is not ProblemData:
        return out

    tests_sorted = sorted(
        filter(
            lambda test: out.should_test(test),
            tests
        ),
        key=lambda test: test.priority,
        reverse=True
    )
    prerun_tests = filter(
        lambda test: test.prerun,
        tests_sorted
    )
    postrun_tests = filter(
        lambda test: not test.prerun,
        tests_sorted
    )

    test_results = []
    def run_tests(test_group):
        for test in test_group:
            result = run_test(out, test)
            test_results.append(result)
            if ("error" in result or len(result["result"]["errors"]) > 0) and test.halt_testing_on_fail:
                return True
        return False
    halted = run_tests(prerun_tests)
    if not halted and "error" not in out.postrun_data():
        run_tests(postrun_tests)
        output = out.run_data["output"]
    else:
        output = None
    
    markdownDisplay = ""
    decorations = []
    for test_result in test_results:
        if "error" in test_result:
            markdownDisplay += f"## Failed Test \"{test_result['context']}\": {test_result['error_type']}\n" \
                + "```json\n" \
                + f"{''.join(test_result['error'])}\n" \
                + "```\n"
            decorations += test_result["decorations"]
            continue
        if len(test_result["output"]) > 0:
            for line in test_result["output"].rstrip().split("\n"):
                print(test_result["name"], "|", line)
        markdownDisplay += test_result["result"]["markdownDisplay"].replace("^[ \t]*#", "##")
        if len(test_result["result"]["errors"]) > 0:
            markdownDisplay += "\n### Design Requirements\n"
            for error in test_result["result"]["errors"]:
                markdownDisplay += f"#### {error['which']}\n" \
                    + f"{error['desc']}\n" \
                    + "```json\n" \
                    + json.dumps(error["context"], sort_keys=True, indent=4) + "\n" \
                    + "```\n"
        decorations += test_result["result"]["decorations"]

    # TODO: Write ChatGPT-fueled text
    #           Redundancy checks
    
    # TODO: Test outputs as decorations?
    #           Redundancy checks
    #           Syntax errors
    #           Output errors (decoration in output editor)
    #           Hints (e.g. range(1,101) instead of range(1,100))
    #           Design requirement failures

    json_out = {"output": output, "markdownDisplay": markdownDisplay, "decorations": decorations}
    if "error" in out.postrun_data():
        exc = _serialize_exception(out.postrun_data()["error"], pretty_syntax_error=True)
        json_out["errors"] = exc
        json_out["markdownDisplay"] += "\n# Error\n```json\n" + "".join(exc) + "\n```\n"
        json_out["decorations"] += _exception_to_decorations(out.postrun_data()["error"])
    if out.mode == "submit":
        json_out["markdownDisplay"] = "Note: Submissions do not currently go into any database, nor are they currently scored.\n\n" \
            + "\n" \
            + json_out["markdownDisplay"]
    return JsonResponse(json_out)

def compile(name, code):
    pass

class ProblemData:
    def __init__(self, mode, main, code, language, active=None, selection=None):
        self.mode = mode
        self.main = main
        self.code = code
        self.language = language
        self.active = active
        self.selection = selection
        self.run_data = None
    def prerun_data(self):
        return {
            "mode": self.mode,
            "main": self.main,
            "code": self.code,
            "language": self.language,
            "active": self.active,
            "selection": self.selection,
        }
    def postrun_data(self):
        data = self.prerun_data()
        if self.run_data is None:
            self.run_data = run_code(self.main, self.code)
        return {
            **self.run_data,
            **data,
        }
    def should_test(self, test):
        if self.mode == "save":
            return test.run_on_save
        elif self.mode == "test":
            return test.run_on_test
        elif self.mode == "hint":
            return test.run_on_hint
        elif self.mode == "submit":
            return test.run_on_submit
        return False

REQUIRED_REQUEST_PARTS = {
    "main": "a `main` module",
    "code": "code",
    "language": "the language the code is run in",
}
OPTIONAL_REQUEST_GROUPS = [{
    "active": "the selected file",
    "selection": "the selected text in the selected file",
}]
def parse_request(request, mode):
    if request.method != "POST":
        return JsonResponse({"error": "invalid_request", "msg": "METHOD must be POST"}, status=405)
    try:
        data_in = json.loads(request.body)
    except json.JSONDecodeError as e:
        return JsonResponse({"error": "invalid_request", "msg": "Invalid JSON", "exception": _serialize_exception(e)}, status=400)

    args = [mode]
    kwargs = {}

    for part, desc in REQUIRED_REQUEST_PARTS.items():
        if part not in data_in:
            return JsonResponse({"error": "invalid_request", "msg": "Must provide" + desc}, status=400)
        else:
            args.append(data_in[part])
    for group in OPTIONAL_REQUEST_GROUPS:
        for part in group:
            if part in data_in:
                has_desc = group[part]
                break;
        else:
            break;
        for part, desc in group.items():
            if part not in data_in:
                return JsonResponse({"error": "invalid_request", "msg": "Included " + has_desc + " but not " + desc}, status=400)
            else:
                kwargs[part] = data_in[part]
    
    return ProblemData(*args, **kwargs)
    
def _run_code(request, test_func, raw=False):
    if request.method != "POST":
        return JsonResponse({"error": "invalid_request", "msg": "METHOD must be POST"}, status=405)
    try:
        data_in = json.loads(request.body)
    except json.JSONDecodeError as e:
        return JsonResponse({"error": "invalid_request", "msg": "Invalid JSON", "exception": _serialize_exception(e)}, status=400)

    if "main" not in data_in:
        return JsonResponse({"error": "invalid_request", "msg": "Must provide a `main` module"}, status=400)
    elif "code" not in data_in:
        return JsonResponse({"error": "invalid_request", "msg": "Must provide code"}, status=400)
    elif "hintsUsed" not in data_in:
        return JsonResponse({"error": "invalid_request", "msg": "Must provide number of hints used"}, status=400)

    main = data_in["main"]
    code = data_in["code"]

    output = run_code(main, code)
    if "error" in output:
        return JsonResponse({
            "error": "caught_exception",
            "when": "compile" if output["error_type"] is SyntaxError else "runtime",
            "exception": _serialize_exception(output["error"], pretty_syntax_error=True),
        })

    if test_func is None or hasattr(test_func, "__call__"):
        test = test_func
    else:
        test = lambda m: \
            _compile_and_import(test_func, "__test__", {**my_globals, "module": m, "main": main, "code": code, "hints": hints_used}, add_print=False).result

    main_module = _compile_and_import(code[main], "__main__", my_globals)
    if raw:
        return main_module
    elif test is None:
        return JsonResponse({"output": main_module.__print_result__})
    else:
        try:
            data = test(main_module)
        except BaseException as e:
            return JsonResponse({"error": "caught_exception", "when": "test", "exception": _serialize_exception(e)}, status=200)
        return JsonResponse(data, status=200)

