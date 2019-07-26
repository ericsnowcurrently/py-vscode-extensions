from collections.abc import Mapping
import os

from .. import util


validator = util.validator


def kind(wrapped):
    def wrapper(raw):
        return wrapped(raw)
    return wrapper


def mapping(key, value):
    def wrapper(raw):
        return util.as_readonly_mapping(raw, key=key, value=value)
    return wrapper


def array(item, *, max=None):
    if max is None:
        max = -1;

    if max < 0:
        def wrapper(raw):
            return util.as_readonly_sequence(raw, item=item)
    else:
        def wrapper(raw):
            if len(raw) > max:
                raise ValueError(f'expected at most {max} items, got {raw!r}')
            return util.as_readonly_sequence(raw, item=item)
    return wrapper


semver = kind(util.SemVer.parse)
verspec = kind(util.VersionSpec.parse)


def person(raw):
    if isinstance(raw, str):
        return util.Person.parse()
    else:
        return util.Person(**raw)


scripts = mapping(validator('npm-script'),
                  validator('nonempty'))


#class Scripts(Mapping):
#    """..."""
#    def __init__(self, scripts):
#        self._scripts = {util.as_str(k): util.as_str(v)
#                         for k, v in scripts.items()}
#
#    def __len__(self):
#        return len(self._scripts)
#
#    def __iter__(self):
#        return iter(self._scripts)
#
#    def __getitem__(self, key):
#        return self._scripts[key]


class Categories:
    """..."""


class Keywords:
    """..."""


class Badge:
    """..."""


class GalleryBanner:
    """..."""


class Contributions:
    """..."""


class Repository:
    """..."""


class Bugs:
    """..."""


# See:
# * https://github.com/ericsnowcurrently/py-vscode-extensions/wiki/3.1-extension-manifest
# * https://code.visualstudio.com/api/references/extension-manifest
# * https://docs.npmjs.com/files/package.json
@util.as_namedtuple(
        # required
        'name',  # also npm
        'publisher',
        'version',  # also npm
        'engines',  # also npm
        # informational
        'license',  # also npm
        # informational (marketplace)
        'displayName',
        'description',
        'categories',
        'keywords',
        'preview',
        'badges',
        'markdown',
        'qna',
        'icon',
        'galleryBanner',
        # technical
        'contributes',
        'activationEvents',
        'extensionDependencies',
        'main',  # also npm
        'dependencies',  # also npm
        'devDependencies',  # also npm
        'scripts',  # also npm
        # other
        'extensionPack',

        # informational (npm-exclusive)
        'author',
        'contributors',
        'homepage',
        'repository',
        'bugs',
        # technical (npm-exclusive)
        #'files',  # [filename]
        #'directories',  # Directories
        #'bin',  # filename or [name: filename]
        #'man', # filename or [filename]
        #'browser',  # replaces "main"
        #'peerDependencies',  # [pkg: ver spec]
        #'bundledDependencies',  # [pkg]
        #'optionalDependencies',  # [pkg: ver spec]
        #'os',  # string
        #'cpu',  # string
        #'private':  # bool
        #'publishConfig':  # object
        )
class Manifest:
    """A single manifest for a VS Code extension."""

    REQUIRED = [
            'name',
            'publisher',
            'version',
            'engines',
            ]
    DEFAULTS = {
            'markdown': 'github',
            'qna': 'marketplace',
            }

    # The default kind is string(required=False).
    KINDS = {
            'name': validator('extension-id'),
            'publisher': validator('nonempty'),
            #'publisher': validator('identifier'),
            'version': semver,
            'engines': mapping(validator('identifier'),
                               verspec),
            'license': validator('license'),
            # displayName
            # description
            'categories': kind(Categories),
            'keywords': kind(Keywords),  # array(str, max=5),
            'preview': validator(bool),
            'badges': array(kind(Badge)),
            'markdown': validator(options=['github', 'standard']),
            'qna': validator(options=['marketplace',
                                     validator('uri'),
                                     False]),
            'icon': validator('filename'),
            'galleryBanner': kind(GalleryBanner),
            # technical
            'main': validator('npm-module'),
            'contributes': kind(Contributions),
            'activationEvents': validator('[event]'),
            'extensionDependencies': validator('[extension-id]'),
            'dependencies': mapping(validator('npm-module'),
                                    validator(options=[verspec,
                                                       validator(kind='filename'),
                                                       validator(kind='uri')])),
            'devDependencies': mapping(validator('npm-module'),
                                       validator(options=[verspec,
                                                          validator(kind='filename'),
                                                          validator(kind='uri')])),
            'scripts': scripts,
            'extensionPack': validator('[extension-id]'),

            'author': kind(person),
            'contributors': array(kind(person)),
            'homepage': validator('uri'),
            'repository': kind(Repository),
            'bugs': kind(Bugs),
            }

    def __new__(cls, *_args, **kwargs):
        defaults = {f: None
                    for f in cls._fields
                    if f not in cls.REQUIRED}
        defaults.update(cls.DEFAULTS)
        args = []
        for field, arg in zip(cls._fields, _args):
            coerce = cls.KINDS[field]
            try:
                args.append(coerce(arg))
            except Exception as exc:
                raise ValueError(f'({field}) {exc}')
            defaults.ppo(field, None)
        args.extend(_args[len(args):])
        for field, value in kwargs.items():
            try:
                coerce = cls.KINDS[field]
            except KeyError:
                continue
            try:
                kwargs[field] = coerce(value)
            except Exception as exc:
                raise ValueError(f'({field}) {exc}')
            defaults.pop(field, None)
        kwargs.update(defaults)
        self = super(Manifest, cls).__new__(cls, *args, **kwargs)
        return self

    def render(self):
        lines = [type(self).__name__ + '(']
        for field, value in zip(self._fields, self):
            lines.append(f'    {field}={value!r}')
        lines.append('    )')
        return os.linesep.join(lines)
