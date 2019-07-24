import configparser
import os
import os.path

from .. import util
from . import _templates
from ._license import get_license


CONFIG = '''
[vscode_ext]
name={name}
version={version}
minvscode={minvscode}
license={license}
author={author}
'''

@util.as_namedtuple('name version minvscode license author')
class Config:
    """The configuration for a single extension project."""

    __slots__ = ()

    VERSION = '0.0.1'
    MIN_VSCODE = '1.36.0'  # 2017-07-23
    LICENSE = 'MIT'

    @classmethod
    def from_file(cls, cfgfile, *,
                  _open=open,
                  ):
        """Return a config matching the given setup.cfg file."""
        if isinstance(cfgfile, str):
            filename = cfgfile
            with _open(filename) as cfgfile:
                return cls.from_file(cfgfile, _open=_open)

        config = configparser.ConfigParser()
        config.read_file(cfgfile)
        raw = dict(config['vscode_ext'])
        return cls(**raw)

    def __new__(cls, name, version=None, minvscode=None,
                license=None, author=None,
                ):
        self = super(cls, cls).__new__(
                cls,
                name=util.coerce_str(name) or None,
                version=util.coerce_str(version) or cls.VERSION,
                minvscode=util.coerce_str(minvscode) or cls.MIN_VSCODE,
                license=util.coerce_str(license).upper() or cls.LICENSE,
                author=util.coerce_str(author) or '',
                )
        return self

    # XXX Always validate?
    #def __init__(self, *args, **kwargs):
    #    self.validate()

    def validate(self):
        if not self.name:
            raise TypeError('missing name')
        # XXX Ensure identifier.

        # "version" is guaranteed to be set.
        # XXX Ensure SemVer?

        # "minvscode" is guaranteed to be set.
        # XXX Ensure valid?

        # "license" is guaranteed to be set.

        # "author" may be any value, including not set.

    def to_file(self, cfgfile, *,
                _open=open,
                ):
        """Write the config out to the given setup.cfg file."""
        if isinstance(cfgfile, str):
            filename = cfgfile
            with _open(filename, 'w') as cfgfile:
                return self.to_file(cfgfile, _open=_open)

        # XXX Use configfile.ConfigFile?
        text = CONFIG.format(**self._asdict())
        cfgfile.write(text)


@util.as_namedtuple('root')
class Files:
    """Info about files/directories for a single extension project."""

    __slots__ = ()

    def __new__(cls, root):
        if root:
            root = os.path.abspath(
                    util.coerce_str(root))
        self = super(cls, cls).__new__(
                cls,
                root=root or None,
                )
        return self

    @property
    def srcdir(self):
        return os.path.join(self.root, 'src')

    @property
    def README(self):
        return os.path.join(self.root, 'README.md')

    @property
    def LICENSE(self):
        return os.path.join(self.root, 'LICENSE')

    @property
    def CHANGELOG(self):
        return os.path.join(self.root, 'CHANGELOG.ms')

    @property
    def cfgfile(self):
        return os.path.join(self.root, 'setup.cfg')

    def validate(self):
        if not self.root:
            raise TypeError('missing root')


@util.as_namedtuple('cfg files')
class Info:
    """Info for a single extension project."""

    __slots__ = ()

    CONFIG = Config
    FILES = Files

    def __new__(cls, cfg, files):
        if isinstance(files, str):
            root = files
            files = cls.FILES(root)
        self = super(cls, cls).__new__(
                cls,
                cfg=cls.CONFIG.from_raw(cfg),
                files=cls.FILES.from_raw(files),
                )
        return self

    def __getattr__(self, name):
        return getattr(self.files, name)

    def validate(self):
        if not self.cfg:
            raise TypeError('missing cfg')
        self.cfg.validate()

        if not self.files:
            raise TypeError('missing files')
        self.files.validate()


def _init_license(filename, cfg):
    year = '2019'  # XXX
    author = cfg.author or 'the authors'
    text = get_license(cfg.license)
    with open(filename, 'w') as outfile:
        outfile.write(f'Copyright {year} {author}\n\n')
        outfile.write(text)


def initialize(cfg, root=None, *,
               _cwd=os.getcwd(),
               _apply_templates=_templates.apply,
               _init_license=_init_license,
               ):
    """Initalize the extension project directory with the given config."""
    cfg = Config.from_raw(cfg)
    if not root:
        root = _cwd
    info = Info(cfg, root)
    # No need to validate.

    # Create the files and directories.
    _apply_templates('project', info.root, cfg._asdict())
    _init_license(info.LICENSE, cfg)

    return info
