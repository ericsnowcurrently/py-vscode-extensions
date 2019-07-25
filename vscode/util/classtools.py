from collections import namedtuple


##################################
# namedtuple

def as_namedtuple(*fields):
    """A class decorator factory for a namedtuple with the given fields."""
    if len(fields) == 1 and not isinstance(fields[0], str):
        fields = fields[0]
    fields = ' '.join(fields)
    def decorator(cls):
        # XXX Support preserving bases?
        assert cls.__bases__ == (object,)
        bases = (
            #cls,
            _NTBase,
            _NTFixes,
            namedtuple(cls.__name__, fields),
            )

        #ns = {'__slots__': ()}
        ns = dict(vars(cls))
        slots = ns.get('__slots__')
        if slots:  # not allowed on tuple subclasses
            ns['__slots__'] = ()
            for name in slots:
                del ns[name]  # Clear the descriptor.
            slotsbase = _new_slots_base(slots)
            bases = (slotsbase,) + bases

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


def _new_slots_base(slots):
    # The state is stored here in a closure.
    instslots = {n: {} for n in slots}
    class _SlotsBase:
        __slots__ = ()
        def __getattr__(self, name):
            # XXX super?
            try:
                return instslots[name][id(self)]
            except KeyError:
                raise AttributeError(name)
        def __setattr__(self, name, value):
            # XXX super?
            try:
                insts = instslots[name]
            except KeyError:
                raise AttributeError(name)
            insts[id(self)] = value
        def __delattr__(self, name):
            # XXX super?
            try:
                insts = instslots[name]
                del insts[id(self)]
            except KeyError:
                raise AttributeError(name)
    return _SlotsBase
