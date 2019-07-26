import re

from .classtools import as_namedtuple, Slot
from .coercion import as_str, as_int, as_sequence


# common
NUMBER = r'(?: 0 | [1-9]\d* )'
WILDCARD = r'(?: x | X | [*] )'
FULL = rf'(?: v? {NUMBER} [.] {NUMBER} [.] {NUMBER} )'

# simple
SIMPLE = rf'''
        (?:
          v?
          ( {NUMBER} )  # major
          [.]
          ( {NUMBER} )  # minor
          [.]
          ( {NUMBER} )  # micro
          )
        '''
SIMPLE_RE = re.compile(rf'''^
        \s*
        {SIMPLE}
        ( .* )  # remainder
        $''', re.VERBOSE)

# semver
# See: https://semver.org/
SEMVER_CHAR = r'[-a-zA-Z0-9]'
SEMVER_IDENTIFIER = rf'''
        (?:
          0 |
          [1-9]\d* |
          \d {SEMVER_CHAR}* [-a-zA-Z] {SEMVER_CHAR}* |
          [a-zA-Z] |
          # XXX Leading / trailing hyphen okay?
          [a-zA-Z] {SEMVER_CHAR}* [a-zA-Z0-9]
          )
        '''
SEMVER_RE = re.compile(rf'''^
        \s*
        {SIMPLE}
        ( [-]
          {SEMVER_IDENTIFIER}
          (?: [.] {SEMVER_IDENTIFIER} )*
          )?  # labels
        ( [+]
          {SEMVER_IDENTIFIER}
          (?: [.] {SEMVER_IDENTIFIER} )*
          )?  # metadata
        \s*
        $''', re.VERBOSE)

# range (spec)
# See:
# * https://docs.npmjs.com/misc/semver#ranges
# * https://docs.npmjs.com/misc/semver#range-grammar
# * https://docs.npmjs.com/files/package.json#dependencies
# XXX Make the regular expressions more exact?
R_PART = rf'(?: {NUMBER} | [-0-9A-Za-z]+ )'
R_QUALIFIER = rf'''
        (?:
          [-] {R_PART} (?: [.] {R_PART} )* |
          [+] {R_PART} (?: [.] {R_PART} )* |
          (?:
            [-] {R_PART} (?: [.] {R_PART} )*
            [+] {R_PART} (?: [.] {R_PART} )*
            )
          )
        '''
R_NUM = rf'(?: {NUMBER} | {WILDCARD} )'
R_PARTIAL = rf'''
        (?:
          {R_NUM} |
          {R_NUM} [.] {R_NUM} |
          {R_NUM} [.] {R_NUM} [.] {R_NUM} {R_QUALIFIER}?
          )
        '''
R_SIMPLE = rf'''
        (?:
          (?: [<=>~^] | >= | <= )?
          {R_PARTIAL}
          )
        '''
SELECTOR_RE = re.compile(rf'''^
        # R_SIMPLE
        ( [<=>~^] | >= | <= )?
        ( {R_NUM} )
        (?:
          [.] ( {R_NUM} )
          (?:
            [.] ( {R_NUM} ) ( {R_QUALIFIER} )?
            )?
          )?
        $''', re.VERBOSE)
R_HYPHEN = rf'''
        (?:
          {R_PARTIAL} \s+ - \s+ {R_PARTIAL}
          )
        '''
RANGE = rf'''
        (?:
          ( {R_HYPHEN} ) |
          ( {R_SIMPLE} (?: \s+ {R_SIMPLE} )* )
          )
        '''
RANGE_RE = re.compile(rf'^{RANGE}$', re.VERBOSE)


def parse(text):
    """Return (major, minor, micro, remainder) for the given text."""
    m = SIMPLE_RE.match(text.strip())
    if not m:
        raise ValueError(f'unsupported version {text!r}')
    return m.groups()


def parse_semver(text):
    """Return (major, minor, micro, labels, metadata) for the given text."""
    m = SEMVER_RE.match(text.strip())
    if not m:
        raise ValueError(f'expected semver, got {text!r}')
    return m.groups()


def parse_spec_version(text):
    """Return (op, major, minor, micro, labels, metadata) for the given text."""
    m = SELECTOR_RE.match(text.strip())
    if not m:
        raise ValueError(f'expected version selector, got {text!r}')
    op, major, minor, micro, qualifier = m.groups()
    if qualifier:
        labels, metadata = qualifier.partition('+')
        labels = tuple(labels[1:].split('.')) if labels else ()
        metadata = tuple(metadata[1:].split('.')) if metadata else ()
    else:
        labels = metadata = None
    return op or None, major, minor, micro, labels, metadata


def normalize_spec_version(version):
    """Return the spec version, normalized."""
    # XXX finish!
    return version


def parse_spec(text):
    """Return [range] for the given text.

    "range" is (min, max), ((op, ver),) or ((op, ver), (op, ver)).
    """
    spec = []
    for raw in text.split('||'):
        raw = raw .strip()
        if not raw:
            spec.append('*')
            continue
        m = RANGE_RE.match(raw)
        if not m:
            raise ValueError(f'expected version range, got {text!r}')
        hyphen, simple = m.groups()
        if hyphen:
            vrange = tuple(parse_spec_version(v.strip())
                           for v in hyphen.split('-'))
            if len(vrange) != 2:
                raise ValueError(f'bad range {raw!r}')
        else:
            vrange = tuple(parse_spec_version(v.strip())
                           for v in simple.split())
            if len(vrange) > 2:
                raise NotImplementedError(raw)
        spec.append(vrange)
    return spec


def normalize_spec(spec):
    """Return the spec with all ranges normalized."""
    # XXX finish!
    return spec


@as_namedtuple('major minor micro')
class _Base:

    __slots__ = ('_raw',)

    @classmethod
    def parse(cls, text):
        """Return a version matching the given text.

        The result is guaranteed to be valid.
        """
        args = cls._parse(text)
        self = cls(*args)
        self._raw = str(text)
        self.validate()
        return self

    @classmethod
    def _parse(cls, text):
        raise NotImplementedError

    def __new__(cls, major, minor, micro):
        self = super(_Base, cls).__new__(
                cls,
                major=as_int(major),
                minor=as_int(minor),
                micro=as_int(micro),
                )
        return self

    def __str__(self):
        try:
            return self._raw
        except AttributeError:
            self._raw = self._as_str()
            return self._raw

    def _as_str(self):
        return '.'.join(self)

    @property
    def patch(self):
        return self.micro

    def validate(self):
        for name, value in zip(self._fields[:3], self):
            if value is None:
                raise TypeError(f'missing {name}')
            if value < 0:
                raise ValueError(f'expected non-negative {name}, got {value}')


class SimpleVersion(_Base):
    """A single version triple."""

    __slots__ = ()

    @classmethod
    def _parse(cls, text):
        *args, remainder = parse(text)
        if remainder.strip():
            raise ValueError(f'expected simple version, got {text!r}')
        return args


class Version(_Base):
    """A single (mostly) SemVer-compatible version.

    The version corresponds to a release.
    """

    #__slots__ = ('_labels',)
    __slots__ = ()
    _labels = Slot()

    @classmethod
    def _parse(cls, text):
        return parse(text)

    @classmethod
    def _parse_labels(cls, raw):
        label = as_str(raw)
        return [label] if label else []

    @classmethod
    def _format_labels(cls, labels):
        if len(labels) == 1:
            return labels[0]
        raise NotImplementedError

    def __new__(cls, major, minor, micro, labels=None):
        self = super().__new__(cls, major, minor, micro)

        if isinstance(labels, str):
            labels = cls._parse_labels(labels)
        elif labels:
            # XXX Handle dict separately?
            labels = as_sequence(labels, item=as_str)
        self._labels = tuple(labels) if labels else None

        return self

    def _as_str(self):
        result = super()._as_str()
        if self._labels:
            result += self._format_labels(self._labels)
        return result

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        try:
            other_labels = other._labels
        except AttributeError:
            other_labels = None
        return self._labels == other_labels

    def __lt__(self, other):
        if super().__lt__(other):
            return True
        if super().__eq__(other) and self._labels:
            try:
                other_labels = other._labels
            except AttributeError:
                other_labels = None
            if not other_labels:
                return True
            return self._labels < other_labels
        return False

    @property
    def labels(self):
        return self._labels

    @property
    def is_stable(self):
        return self.major > 0

    @property
    def is_final(self):
        return self._labels is None

    def validate(self):
        super().validate()

        # "labels" is allowed to be missing, but individual labels are not.
        for i, label in enumerate(self._labels or ()):
            if not label:
                raise ValueError(f'missing label #{i}')


class SemVer(Version):
    """A single SemVer-compatible version.

    The version corresponds to a release.
    """
    # See: https://semver.org/

    #__slots__ = ('_metadata',)
    __slots__ = ()
    _metadata = Slot()

    @classmethod
    def _parse(cls, text):
        return parse_semver(text)

    @classmethod
    def _parse_labels(cls, raw):
        if raw.startswith('-'):
            raw = raw[1:]
        return raw.split('.')

    @classmethod
    def _format_labels(cls, labels):
        return '-' + '.'.join(labels)

    def __new__(cls, major, minor, micro, labels=None, metadata=None):
        self = super().__new__(cls, major, minor, micro, labels)

        if isinstance(metadata, str):
            metadata = metadata.strip().split('.')
        elif metadata:
            # XXX Handle dict separately?
            metadata = as_sequence(metadata, item=as_str)
        self._metadata = tuple(metadata) if metadata else None

        return self

    def _as_str(self):
        result = super()._as_str()
        if self._metadata:
            result += '+' + '.'.join(self._metadata)
        return result

    @property
    def metadata(self):
        return self._metadata

    def validate(self):
        super().validate()

        # "metadata" is allowed to be missing, but individual items are not.
        for i, item in enumerate(self._metadata or ()):
            if not item:
                raise ValueError(f'missing metadata item #{i}')


@as_namedtuple('major minor micro labels metadata op')
class SpecVersion:
    """A single SemVer-compatible version selector (matcher)."""

    __slots__ = ('_raw',)

    @classmethod
    def parse(cls, text):
        """Return a VersionSpec matching the given text.

        The result is guaranteed to be valid.
        """
        version = parse_spec_version(text)
        (op, major, minor, micro, labels, metadata
         ) = normalize_spec_version(version)
        self = cls(major, minor, micro, labels, metadata, op)
        self._raw = str(text)
        self.validate()
        return self

    def __new__(cls, major, minor=None, micro=None, labels=None, metadata=None,
                op=None):
        self = super(SpecVersion, cls).__new__(
                cls,
                major=as_int(major),
                minor=as_int(minor),
                micro=as_int(micro),
                labels=tuple(as_sequence(labels, item=as_str)),
                metadata=tuple(as_sequence(metadata, item=as_str)),
                op=as_str(op) or None,
                )

    def __str__(self):
        try:
            return self._raw
        except AttributeError:
            self._raw = self._as_str()
            return self._raw

    def _as_str(self):
        result = '.'.join(d for d in self.simple if d)
        if self.op:
            result = self.op + result
        if self.labels:
            result += '-' + '.'.join(self.labels)
        if self.metadata:
            result += '+' + '.'.join(self.metadata)
        return result

    @property
    def simple(self):
        return (self.major, self.minor, self.mirco)

    def validate(self):
        raise NotImplementedError


@as_namedtuple('min max')
class VersionRange:
    """A range of versions."""


class VersionSpec(str):
    """A single SemVer-compatible version specifier (matcher)."""
    # See:
    # * https://docs.npmjs.com/files/package.json#dependencies
    # * https://docs.npmjs.com/misc/semver#ranges

    __slots__ = ('_ranges',)

    @classmethod
    def parse(cls, text):
        """Return a spec matching the given text.

        The result is guaranteed to be valid.
        """
        text = text.strip()
        self = cls(text)
        spec = parse_spec(text)
        self._ranges = normalize_spec(spec)
        self.validate()
        return self

    @property
    def ranges(self):
        try:
            return self._ranges
        except AttributeError:
            spec = parse_spec(self)
            self._ranges = normalize_spec(spec)
            return self._ranges

    def validate(self):
        # XXX finish!
        return
