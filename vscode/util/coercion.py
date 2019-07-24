
def as_str(raw):
    """Return a string for the given raw value."""
    if not raw:
        return ''
    return str(raw)


def as_int(raw):
    """Return an int for the given raw value.

    Return None for "falsey", non-zero values.
    """
    if raw == 0:
        return 0
    elif not raw:
        return None
    else:
        return int(raw)


def iter_sequence(raw, *, item=None):
    """Yield each coerced item in the raw value."""
    if item is None:
        return iter(raw)
    else:
        return iter(item(v) for v in raw)


def iter_mapping(raw, *, key=None, value=None):
    """Yield each coerced item in the raw value."""
    try:
        get_items = raw.items
    except AttributeError:
        items = raw
    else:
        items = get_items()

    if key is None:
        if value is None:
            return iter((k, v) for k, v in items)
        else:
            return iter((k, value(v)) for k, v in items)
    elif value is None:
        return iter((key(k), v) for k, v in items)
    else:
        return iter((key(k), value(v)) for k, v in items)


def as_sequence(raw, *, item=None, cls=list):
    """Return a coerced sequence for the given raw value."""
    return cls(
            iter_sequence(raw, item=item))


def as_readonly_sequence(raw, *, item=None):
    """Return a coerced sequence for the given raw value.

    The returned container type is not guaranteed.  The only guarantee
    is that it will be read-only.
    """
    return as_sequence(raw, item=item, cls=tuple)


def as_mapping(raw, *, key=None, value=None, cls=dict):
    """Return a coerced mapping for the given raw value."""
    return cls(
            iter_mapping(raw, key=key, value=value))


def as_readonly_mapping(raw, *, key=None, value=None, cls=dict):
    """Return a coerced mapping for the given raw value.

    The returned container type is not guaranteed.  The only guarantee
    is that it will be read-only.
    """
    return types.MappingProxyType(
        as_mapping(raw, key=key, value=value))
