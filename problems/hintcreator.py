import RestrictedPython
import re

from .runcode import OwnRestrictingNodeTransformer, run_code

def get_help(request, selection):
    module = run_code(request, None)
    if not any(char.isspace() for char in selection):
        subparts = selection.split(".")
        piece = module
        for subpart in subparts:
            if hasattr(piece, subpart):
                piece = getattr(piece, subpart)
            else:
                return None

