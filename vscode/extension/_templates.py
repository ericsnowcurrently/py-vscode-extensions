import os
import os.path
import re

from .. import util
from . import TEMPLATES


UNESCAPED_RE = re.compile('''
        (?:
          (?: ^ | [^{] )
          [{]
          (?: [^{] | $ )
          ) |
        (?:
          (?: ^ | [^}] )
          [}]
          (?: [^}] | $)
          )
        ''', re.VERBOSE)


def apply_to_tree(kind, rootdir, ns, *,
                  _walk=os.walk,
                  _mkdirs=os.makedirs,
                  _read_all=util.read_all,
                  _write_all=util.write_all,
                  ):
    templates = os.path.join(TEMPLATES, kind)
    for root, subdirs, files in _walk(templates):
        relroot = root[len(templates):].lstrip(os.path.sep)
        for name in subdirs:
            dirname = os.path.join(rootdir, relroot, name)
            #logger.info(f'creating project subdirectory at {dirname!r}')
            try:
                _mkdirs(dirname)
            except FileExistsError:
                pass
        for name in files:
            if name.startswith('.') and name.endswith('.swp'):  # vim
                continue
            source = os.path.join(root, name)
            target = os.path.join(rootdir, relroot, name)
            #logger.info(f'applying project template at {target!r}')
            template = _read_all(source)
            text = '\n'.join(
                    _apply_lines(source, template, ns))
            _write_all(target, text)


def _apply_lines(filename, template, ns):
    for line in template.splitlines():
        try:
            yield line.format(**ns)
        except Exception as exc:
            msg = (f'problem applying template file {filename!r} '
                   f'({type(exc).__name__}: {exc})')
            if type(exc) is ValueError and UNESCAPED_RE.search(line):
                msg += ' (try escaping the bracket in the template)'
            raise Exception(msg)
