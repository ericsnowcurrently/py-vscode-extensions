from collections import namedtuple


_NOT_SET = object()


class classonly:
    """A non-data descriptor that makes a value only visible on the class.

    This is like the "classmethod" builtin, but does not show up on
    instances of the class.  It may be used as a decorator.
    """

    def __init__(self, obj):
        self.obj = obj
        self.getter = classmethod(obj).__get__
        self.name = None

    def __repr__(self):
        return f'{type(self).__name__}(obj={self.obj!r})'

    def __set_name__(self, cls, name):
        if self.name is not None:
            raise TypeError('already used')
        self.name = name

    def __get__(self, obj, cls):
        if obj is not None:
            raise AttributeError(self.name)
        # called on the class
        return self.getter(None, cls)


class FieldsMismatchError(NotImplementedError):
    pass

class UnsupportedTypeError(NotImplementedError):
    pass


class HasRawFactory:

    __slots__ = ()

    #ARG_NAMES = ...

    @classonly
    def from_raw(cls, raw):
        if not raw:
            return None
        elif isinstance(raw, cls):
            return raw
        elif isinstance(raw, str):
            return cls.from_string(raw)
        elif hasattr(type(raw), '__next__'):
            return cls.from_iterator(raw)
        else:
            argnames = getattr(cls, '_ARG_NAMES', None)
            if argnames is None:
                argnames = getattr(cls, '_fields', None)
            self = cls._from_mapping(raw, argnames)
            if self is not None:
                return self
            else:
                self = cls._from_sequence(raw, argnames)
                if self is not None:
                    return self
                raise UnsupportedTypeError(raw)

    @classonly
    def from_string(cls, value):
        """Return a new instance based on the given string."""
        raise NotImplementedError

    @classonly
    def mapping_to_kwargs(cls, value, argnames):
        if not hasattr(value, 'items'):
            return None
        return value

    @classonly
    def sequence_to_args(cls, value, argnames):
        return value

    @classonly
    def _from_mapping(cls, value, argnames):
        kwargs = cls.mapping_to_kwargs(raw, argnames)
        if kwargs is None:
            return None

        try:
            return cls(**kwargs)
        except TypeError:
            try:
                dict(**kwargs)
            except TypeError:
                return None
            failed = (value, kwargs)
            if argnames is not None:
                if len(kwargs) != len(argnames):
                    raise FieldsMismatchError(failed)
                if set(kwargs) != set(argnames):
                    raise FieldsMismatchError(failed)
            raise  # re-raise

    @classonly
    def _from_sequence(cls, value, argnames):
        args = cls.sequence_to_args(value, argnames)
        if args is None:
            return None

        try:
            return cls(*args)
        except TypeError:
            try:
                tuple(*args)
            except TypeError:
                return None
            failed = (value, args)
            if len(args) != len(argnames):
                raise FieldsMismatchError(failed)
            raise  # re-raise


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
        return value

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

def as_namedtuple(*fields, extras=True):
    """A class decorator factory for a namedtuple with the given fields.

    If any decorators with side effects (e.g. registration) were
    already applied then using this is problematic.
    """
    if len(fields) == 1 and not isinstance(fields[0], str):
        fields = fields[0]
    fields = ' '.join(fields)

    bases = (
        _NTFixes,
        namedtuple('NTBase', fields),
    )
    if extras:
        bases += (_NTExtras,)

    def decorator(cls):
        meta = type(cls)
        if meta is not type:
            raise NotImplementedError
        # XXX Support preserving bases?
        if cls.__base__ is not object:
            raise NotImplementedError

        # If any decorators with side effects (e.g. registration) were
        # already applied then the following is problematic.
        ns = dict(vars(cls))
        _fix_slots(ns)
        NT = meta(cls.__name__, bases, ns)
        #NT = meta(cls.__name__, (cls,) + bases, ns)
        #class NT(cls, *bases, metaclass=meta):
        #    __slots__ = ()
        NT.__name__ = cls.__name__
        # XXX Ensure that they are in the same file/scope?
        NT.__module__ = cls.__module__
        NT.__qualname__ = cls.__qualname__
        NT.__doc__ = cls.__doc__
        return NT
    return decorator


class _NTFixes:

    __slots__ = ()

    # The default _make() is not subclass-friendly.
    @classmethod
    def _make(cls, iterable):
        return cls.__new__(cls, *iterable)

    # The default in older Python versions is not subclass-friendly.
    def __repr__(self):
        _, _, sig = super().__repr__().partition('(')
        return f'{self.__class__.__name__}({sig}'

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

    # The default never triggers __init__().
    def _replace(self, **kwargs):
        obj = super()._replace(**kwargs)
        obj.__init__()
        # XXX Always validate()?
        #if hasattr(obj, 'validate'):
        #    obj.validate()
        return obj


class _NTExtras(HasRawFactory):

    __slots__ = ()

    # XXX Always validate?
    #def __init__(self, *args, **kwargs):
    #    self.validate()

    def validate(self):
        return
