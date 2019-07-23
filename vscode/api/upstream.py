import io
import os.path
import pprint
import sys
import urllib.request

from .. import typescript
from . import DATADIR


FILENAME = 'vscode{ref}{channel}.d.ts'
CHANNELS = ('stable', 'proposed')

URL_BASE = 'https://raw.githubusercontent.com/microsoft/vscode/{ref}/src/vs/'


def open(channel='stable', *,
         ref='master',
         cached=True,
         _open_cached=lambda ch, ref: open_cached(ch, ref=ref),
         _open_upstream=lambda ch, ref: open_upstream(ch, ref=ref),
         _write_local=lambda t, c, ch, ref: write_local(t, c, ch, ref=ref),
         _open=__builtins__.open,
         ):
    """Return the text of the upstream vscode.d.ts file."""
    # First look for a cached copy.
    file = _open_cached(channel, ref)
    if file is not None:
        return file

    # Fall back to upstream.
    file = _open_upstream(channel, ref)
    if cached:
        filename = _write_local(file, cached, channel, ref)
        file = _open(filename)
    return file


def _resolve_filename(channel='stable', ref='master'):
    if not channel:
        channel = 'stable'
    if not ref:
        ref = 'master'
    return FILENAME.format(
            ref='' if ref == 'master' else ('.' + ref),
            channel='' if channel == 'stable' else ('.' + channel),
            )


##################################
# cached

def resolve_cached(channel='stable', ref='master'):
    """Return the filename where the cached vscode.d.ts should be."""
    filename = _resolve_filename(channel, ref)
    return os.path.join(DATADIR, filename)


def open_cached(channel='stable', mode='r', *,
                ref='master',
                _resolve=resolve_cached,
                _open=__builtins__.open,
                ):
    """Return an open text file for the matching cached vscode.d.ts file."""
    filename = _resolve(channel, ref)
    try:
        return _open(filename, mode)
    except Exception:
        if mode == 'r' and not os.path.exists(filename):
            return None
        raise


def write_local(text, cached=None, channel='stable', *,
                ref='master',
                _open_cached=open_cached,
                _open=__builtins__.open,
                ):
    """Write the given text out to the matching cache location."""
    if not cached or cached is True:
        outfile = _open_cached(channel, 'w', ref=ref)
    else:
        outfile = _open(cached, 'w')
    with outfile:
        if isinstance(text, str):
            outfile.write(text)
        else:
            for line in text:
                outfile.write(line)
    return outfile.name


def clear_cache(channel=None, ref=None, *,
                _resolve=resolve_cached,
                _rmfile=None,
                ):
    """Remove all matching cached files."""
    raise NotImplementedError


##################################
# downloaded

#URLS = {
#        'stable': 'https://github.com/microsoft/vscode/blob/{ref}/src/vs/vscode.d.ts',
#        'proposed': 'https://github.com/microsoft/vscode/blob/{ref}/src/vs/vscode.proposed.d.ts',
#        }

def resolve_upstream(channel='stable', ref='master'):
    """Return the vscode.d.ts URL to use for the given channel."""
    name = _resolve_filename(channel)
    return URL_BASE.format(ref=ref or 'master') + name


def open_upstream(channel='stable', *,
                  ref='master',
                  _resolve=resolve_upstream,
                  _urlopen=urllib.request.urlopen,
                  ):
    """Return an open text file for the matching upstream vscode.d.ts file."""
    url = _resolve(channel, ref)
    resp = _urlopen(url)
    return io.TextIOWrapper(resp)


##################################
# the script

def _show_api_info(api, depth=0, indent='  ', maxdepth=None):
    if maxdepth and depth > maxdepth:
        return
    _indent = indent * depth
    for name, value in api.items():
        if name in ('_kind', '_raw', '_isarray'):
            continue
        if isinstance(value, list):
            for raw in value:
                print(_indent + '{:10} {}'.format(name, raw))
            continue

        if value['_kind'] == 'inline':
            if value.get('_isarray'):
                print(_indent + '{:10} (array) {!r}'.format(name, value['_raw']))
            else:
                print(_indent + '{:10} {!r}'.format(name, value['_raw']))
        else:
            print(_indent + '{:10} ({}) {!r}'.format(name, value['_kind'], value['_raw']))
        _show_api(value, depth + 1, indent, maxdepth)


def _flatten(api):
    remainder = [('', api)]
    while remainder:
        parent, ns = remainder.pop()
        for name, value in ns.items():
            if name in ('_kind', '_raw', '_isarray'):
                continue
            if parent:
                name = parent + '.' + name
            if isinstance(value, list):
                if '(' in value[0]:
                    yield name, 'func'
                else:
                    yield name, 'prop'
            elif value['_kind'] == 'inline':
                yield name, 'prop'
            else:
                yield name, value['_kind']
                remainder.append((name, value))


def _show_api_names(api):
    for name, kind in sorted(_flatten(api)):
        kind = ' ' * name.count('.') + kind
#        if kind in ('func', 'prop'):
#            kind = ' ' + kind
        print('{:10} {}'.format(kind, name))


def parse_args(prog=sys.argv[0], argv=sys.argv[1:]):
    return {}


def main():
    with open() as upstream:
        api = typescript.parse_declarations(upstream)
    _show_api_names(api)
    #_show_api(api, maxdepth=1)
    #pprint.pprint(api)


if __name__ == '__main__':
    kwargs = parse_args()
    main(**kwargs)
