import re


def match(regex, text):
    """Return the match object (or None).

    The pattern must match exactly and is treated as verbose.
    """
    if isinstance(regex, str):
        return re.match(rf'^{regex}$', text, re.VERBOSE)
    else:
        return regex.match(text)


