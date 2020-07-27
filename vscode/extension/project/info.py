import configparser
import os
import os.path

from vscode import util


CONFIG = '''
[vscode_ext]
name={name}
version={version}
minvscode={minvscode}
license={license}
author={author}
publisher={publisher}
repo={repo}
'''


@util.as_namedtuple(
        'name',
        'version',
        'minvscode',
        'license',
        'author',
        'publisher',
        'repo',
        )
class Config:
    """The configuration for a single extension project."""

    __slots__ = ()

    VERSION = '0.0.1'
    MIN_VSCODE = '1.36.0'  # 2017-07-23
    LICENSE = 'MIT'
    PUBLISHER = '???'
    REPO = '???'

    @classmethod
    def from_file(cls, cfgfile, *,
                  _open=open,
                  ):
        """Return a config matching the given setup.cfg file.

        The result is guaranteed to be valid.
        """
        if isinstance(cfgfile, str):
            filename = cfgfile
            with _open(filename) as cfgfile:
                return cls.from_file(cfgfile)

        ini = configparser.ConfigParser()
        ini.read_file(cfgfile)
        raw = dict(ini['vscode_ext'])
        self = cls(**raw)
        self.validate()
        return self

    def __new__(cls,
                name,
                version=None,
                minvscode=None,
                license=None,
                author=None,
                publisher=None,
                repo=None,
                *,
                _get_author=util.get_git_committer,
                _get_repo=util.get_git_repo_url,
                ):
        if not author:
            author = _get_author()
        if not repo:
            repo = _get_repo()
            if not repo:
                gh_user = '???'
                repo = f'https://github.com/{gh_user}/{name}'
        self = super(Config, cls).__new__(
                cls,
                name=util.as_str(name) or None,
                version=util.as_str(version) or cls.VERSION,
                minvscode=util.as_str(minvscode) or cls.MIN_VSCODE,
                license=util.as_str(license).upper() or cls.LICENSE,
                author=util.Person.from_raw(author) if author else '',
                publisher=util.as_str(publisher) or cls.PUBLISHER,
                repo=util.as_str(repo) or cls.REPO,
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
                return self.to_file(cfgfile)

        # XXX Use configfile.ConfigFile?
        text = CONFIG.format(**self._asdict())
        cfgfile.write(text)


@util.as_namedtuple('root')
class Files:
    """Info about files/directories for a single extension project."""

    __slots__ = ()

    @classmethod
    def from_raw(cls, raw):
        """Return a Files that matches the given value.

        The result (if not None) is guaranteed to be valid.
        """
        if isinstance(raw, str):
            return cls(raw)
        else:
            return super(Files, cls).from_raw(raw)

    def __new__(cls, root, *,
                _cwd=os.getcwd(),
                ):
        root = util.resolve_filename(
                util.as_str(root))
        self = super(Files, cls).__new__(
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
class Project:
    """Info for a single extension project."""

    __slots__ = ()

    CONFIG = Config
    FILES = Files

    @classmethod
    def from_raw(cls, raw, **kwargs):
        """Return a projectthat matches the given value.

        The result (if not None) is guaranteed to be valid.
        """
        try:
            return cls.from_files(raw, **kwargs)
        except ValueError:
            return super(Project, cls).from_raw(raw)

    @classmethod
    def from_files(cls, files, *,
                   cfg=None,
                   ):
        """Return info for the project at the given root.

        The result is guaranteed to be valid.
        """
        files = cls.FILES.from_raw(files or _cwd)
        # No need to validate.
        if not cfg:
            cfg = cls.CONFIG.from_file(files.cfgfile)
            # No need to validate.
        elif not isinstance(cfg, cls.CONFIG):
                raise ValueError(f'expected {cls.CONFIG}, got {cfg!r}')
        return cls(cfg, files)

    def __new__(cls, cfg, files):
        self = super(Project, cls).__new__(
                cls,
                cfg=cls.CONFIG.from_raw(cfg),
                files=cls.FILES.from_raw(files),
                )
        return self

    def __getattr__(self, name):
        try:
            return super(Project, self).__getattr__(name)
        except AttributeError:
            return getattr(self.files, name)

    def validate(self):
        if not self.cfg:
            raise TypeError('missing cfg')
        self.cfg.validate()

        if not self.files:
            raise TypeError('missing files')
        self.files.validate()
