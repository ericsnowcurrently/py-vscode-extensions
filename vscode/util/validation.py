

def validate(value, *, kind=None, options=None):
    """Return the value after ensuring it is valid."""
    if kind is None:
        if options is None:
            kind = 'nonempty'
    elif options is not None:
        raise ValueError('expected kind or options, got both')

    if options:
        _validate_options(value, options)
        return value

    if isinstance(kind, type):
        if type(value) is not kind:
            raise ValueError(f'expected {kind.__name__}, got {value!r}')
    elif callable(kind):
        kind(value)
    elif not isinstance(kind, str):
        raise ValueError(f'unsupported kind {kind!r}')
    elif kind.startswith('[') and kind.endswith(']'):
        kind = kind[1:-1]
        validate_sequence(value, kind=kind)
    else:
        _validate_string(value, kind)
    return value


def validate_sequence(items, *, kind=None, options=None):
    """Validate each item in the sequence."""
    for item in items:
        validate(item, kind=kind, options=options)


def _validate_options(value, options):
    for opt in options:
        if isinstance(opt, type):
            if type(value) is opt:
                return
        elif callable(opt):
            try:
                opt(value)
            except (TypeError, ValueError):
                continue
            return
        elif value == opt:
            return
    else:
        if len(options) == 1:
            opt = options[0]
            raise ValueError(f'expected {opt!r}, got {value!r}')
        else:
            raise ValueError(f'expected one of several options, got {value!r}')


def _validate_string(value, kind):
    if kind == 'nonempty':
        raise NotImplementedError
    elif kind == 'identifier':
        raise NotImplementedError
    elif kind == 'filename':
        raise NotImplementedError
    elif kind == 'uri':
        # XXX finish
        return
    elif kind == 'email':
        # XXX finish
        return
    elif kind == 'license':
        raise NotImplementedError

    # app-specific
    elif kind == 'npm-module':
        raise NotImplementedError
    elif kind == 'extension-id':
        raise NotImplementedError
    elif kind == 'event':
        raise NotImplementedError
    else:
        raise ValueError(f'unsupported kind {kind!r}')


def validator(kind=None, options=None):
    """Return a wrapper around validate()."""
    def wrapper(value):
        return validate(value, kind=kind, options=options)
