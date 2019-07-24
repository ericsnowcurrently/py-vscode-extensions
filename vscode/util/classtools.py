from collections import namedtuple


##################################
# namedtuple

def as_namedtuple(*fields):
    """A class decorator factory for a namedtuple with the given fields."""
    fields = ' '.join(fields)
    def decorator(cls):
        assert cls.__bases__ == (object,)
        bases = (
            #cls,
            _NTBase,
            _NTFixes,
            namedtuple(cls.__name__, fields),
            )
        #ns = {'__slots__': True}
        ns = dict(vars(cls))
        # Note: This ignores any metaclass
        return type(cls.__name__, bases, ns)
    return decorator


class _NTBase:

    __slots__ = ()

    @classmethod
    def from_raw(cls, raw):
        """Return an instance that matches the given value.

        The result (if not None) is guaranteed to be valid.
        """
        if isinstance(raw, cls):
            return raw
        elif not raw:
            return None
        else:
            raise ValueError(f'unsupported raw value {raw!r}')

    # To make sorting work with None:
    def __lt__(self, other):
        try:
            return super().__lt__(other)
        except TypeError:
            if None in self:
                return True
            elif None in other:
                return False
            else:
                raise


class _NTFixes:

    __slots__ = ()

    @classmethod
    def _make(cls, iterable):  # The default is not subclass-friendly.
        return cls.__new__(cls, *iterable)

    def __repr__(self):  # The default is not subclass-friendly.
        _, _, sig = super().__repr__().partition('(')
        return f'{self.__class__.__name__}({sig}'

    def _replace(self, **kwargs):  # The default never triggers __init__().
        obj = super()._replace(**kwargs)
        obj.__init__()
        # XXX Always validate()?
        #if hasattr(obj, 'validate'):
        #    obj.validate()
        return obj
