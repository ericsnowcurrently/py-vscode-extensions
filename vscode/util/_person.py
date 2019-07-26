from .classtools import as_namedtuple
from .coercion import as_str
from .validation import validate
from .net import EMAIL, URL
from .regex import match


PERSON = rf'''
        (?:
          ( [^<(\s] [^<(]* )  # name
          (?:
            [<]
            (?: ({EMAIL}) | ([^>\s]+) )
            [>]
            )?
          (?:
            [(]
            (?: ({URL}) | ([^)\s]+) )
            [)]
            )?
          )
        '''


def parse_person(text):
    """Return (name, email, url) for the given text.

    The values are essentially unvalidated (other than having roughly
    matched a regex).
    """
    m = match(PERSON, text)
    if not m:
        return None
    name, email, _email, url, _url = m.groups()
    return (
            name,
            email or _email or None,
            url or _url or None,
            )


@as_namedtuple('name email url')
class Person:
    """Information about a single person."""

    __slots__ = ('_raw',)

    @classmethod
    def from_raw(cls, raw):
        if isinstance(raw, str):
            return cls.parse(raw)
        else:
            return super(Person, cls).from_raw(raw)

    @classmethod
    def parse(cls, text):
        """Return the Person for the given text.

        The result (if not None) is guaranteed to be valid.
        """
        text = text.strip()
        args = parse_person(text)
        self = cls(*args)
        self._raw = text
        self.validate()
        return self

    def __new__(cls, name, email=None, url=None):
        self = super(Person, cls).__new__(
                cls,
                name=as_str(name) or None,
                email=as_str(email) or None,
                url=as_str(url) or None,
                )
        return self

    def __str__(self):
        try:
            return self._raw
        except AttributeError:
            self._raw = self._as_str()
            return self._raw

    def _as_str(self):
        if self.email:
            if self.url:
                return f'{self.name} <{self.email}> ({self.url})'
            else:
                return f'{self.name} <{self.email}>'
        elif self.url:
            return f'{self.name} ({self.url})'
        else:
            return self.name

    def validate(self):
        if not self.name:
            raise TypeError('missing name')

        # email can be missing.
        if self.email:
            validate(self.email, kind='email')

        # url can be missing.
        if not self.url:
            validate(self.url, kind='uri')
