import re


def match(pat, text):
    """Return the match object (or None).

    The pattern must match exactly and is treated as verbose.
    """
    return re.match(rf'^{pat}$', text, re.VERBOSE)


