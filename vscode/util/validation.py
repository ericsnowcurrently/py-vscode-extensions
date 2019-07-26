from .net import EMAIL, URL
from .regex import match


def validator(kind=None, options=None):
    """Return a wrapper around validate()."""
    def wrapper(value):
        return validate(value, kind=kind, options=options)
    return wrapper


def validate(value, name=None, *, kind=None, options=None):
    """Return the value after ensuring it is valid."""
    if kind is None:
        if options is None:
            kind = 'nonempty'
    elif options is not None:
        raise ValueError('expected kind or options, got both')

    if options:
        err = _validate_by_options(value, options)
    else:
        err = _validate_by_kind(value, kind)
    if err:
        if name:
            err = f'({name}) {err}'
        raise ValueError(err)
    return value


def validate_sequence(items, name=None, *, kind=None, options=None):
    """Validate each item in the sequence."""
    err = _validate_sequence(items, kind, options)
    if err:
        if name:
            err = f'({name}) {err}'
        raise ValueError(err)
    return items


def _validate_sequence(items, kind, options):
    for item in items:
        err = validate(item, kind=kind, options=options)
        if err:
            return err
        if item is None:
            return 'missing item'
    else:
        return None


def _validate_by_kind(value, kind):
    if isinstance(kind, type):
        if type(value) is not kind:
            return f'expected {kind.__name__}, got {value!r}'

    elif callable(kind):
        return kind(value)

    elif not isinstance(kind, str):
        raise ValueError(f'unsupported kind {kind!r}')
    elif kind.startswith('[') and kind.endswith(']'):
        kind = kind[1:-1]
        return _validate_sequence(value, kind, ())
    elif isinstance(value, str):
        return _validate_string(value, kind)

    elif value is not None:
        return f'unsupported value {value!r}'

    return None


def _validate_by_options(value, options):
    for opt in options:
        if isinstance(opt, type):
            if type(value) is opt:
                return None
        elif callable(opt):
            try:
                opt(value)
            except (TypeError, ValueError):
                continue
            return None
        elif value == opt:
            return None
    else:
        if len(options) == 1:
            opt = options[0]
            return f'expected {opt!r}, got {value!r}'
        else:
            return f'expected one of several options, got {value!r}'


def _validate_string(value, kind):
    if kind == 'nonempty':
        if not value:
            return f'expected non-empty string, got {value!r}'

    #elif not value:
    #    return None
    elif kind == 'identifier':
        if not value.isidentifier():
            return f'expected identifier, got {value!r}'
    elif kind == 'filename':
        # XXX Be more specific?
        if not value:
            return f'expected non-empty string, got {value!r}'
    elif kind == 'uri':
        if not match(URL, value):
            return f'expected URL, got {value!r}'
    elif kind == 'email':
        if not match(EMAIL, value):
            return f'expected email address, got {value!r}'
    elif kind == 'license':
        # XXX Be more specific?
        if not value:
            return f'expected non-empty string, got {value!r}'

    # app-specific
    elif kind == 'npm-script':
        # XXX Be more specific?
        if not value:
            return f'expected non-empty string, got {value!r}'
    elif kind == 'npm-module':
        # XXX Be more specific?
        if not value:
            return f'expected non-empty string, got {value!r}'
    elif kind == 'extension-id':
        # XXX Be more specific?
        if not value:
            return f'expected non-empty string, got {value!r}'
    elif kind == 'event':
        # XXX Be more specific?
        if not value:
            return f'expected non-empty string, got {value!r}'
    else:
        raise ValueError(f'unsupported kind {kind!r}')
