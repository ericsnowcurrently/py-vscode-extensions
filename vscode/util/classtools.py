from collections import namedtuple


_NOT_SET = object()


##################################
# slots

class Slot:
    """A descriptor that provides a slot."""

    __slots__ = ('initial', 'default', 'readonly', 'instances', 'name')

    def __init__(self, initial=_NOT_SET, *,
                 default=_NOT_SET,
                 readonly=False,
                 ):
        self.initial = initial
        self.default = default
        self.readonly = readonly

        self.instances = {}
        self.name = None

    def __set_name__(self, cls, name):
        if self.name is not None:
            raise TypeError('already used')
        self.name = name

    def __get__(self, obj, cls):
        if obj is None:  # called on the class
            return self
        try:
            value = self.instances[id(obj)]
        except KeyError:
            value = self.default if self.initial is _NOT_SET else self.initial
            self.instances[id(obj)] = value
        if value is _NOT_SET:
            raise AttributeError(self.name)

    def __set__(self, obj, value):
        if self.readonly:
            raise AttributeError(f'{self.name} is readonly')
        self.instances[id(obj)] = value

    def __delete__(self, obj):
        if self.readonly:
            raise AttributeError(f'{self.name} is readonly')
        self.instances[id(obj)] = self.default


def set_slots(cls, *names, **defaults):
    """Set pseudo-slots on the given class (in lieu of __slots__.

    The slots are added to the class as descriptors.

    This is espcially useful for subclasses of types that do not support
    slots (like tuple).
    """
    for name in names:
        setattr(cls, name, Slot())
    for name, default in defaults.items():
        setattr(cls, name, Slot(default=default))


def slots(*names, **defaults):
    """A class decorator (factory) for setting slots """
    def decorator(cls):
        set_slots(cls, *names, **defaults)
        return cls
    return decorator


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


def _fix_slots(ns, bases=None, slots=()):
    __slots__ = ns.get('__slots__')
    if slots and ns.__slots__:
        raise TypeError('got unexpected __slots__')
    slots = slots or __slots__
    if slots:  # not allowed on tuple subclasses
        ns['__slots__'] = ()
        if bases is None:
            for name in slots:
                # XXX Make sure it is actually a descriptor?
                ns[name] = Slot()
        else:
            for name in slots:
                # XXX Make sure it is actually a descriptor?
                ns.pop(name, None)  # Clear the descriptor.
            slotsbase = _new_slots_base(slots)
            bases = (slotsbase,) + bases
    return bases


##################################
# namedtuple

def as_namedtuple(*fields, slots=()):
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
        #bases = _fix_slots(ns, bases)
        _fix_slots(ns)

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
