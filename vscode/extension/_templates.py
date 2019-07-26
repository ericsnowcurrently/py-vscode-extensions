import os
import os.path

from . import TEMPLATES


def apply(kind, rootdir, ns):
    templates = os.path.join(TEMPLATES, kind)
    for root, subdirs, files in os.walk(templates):
        relroot = root[len(templates):].lstrip(os.path.sep)
        for name in subdirs:
            dirname = os.path.join(rootdir, relroot, name)
            #logger.info(f'creating project subdirectory at {dirname!r}')
            try:
                os.makedirs(dirname)
            except FileExistsError:
                pass
        for name in files:
            if name.startswith('.') and name.endswith('.swp'):  # vim
                continue
            source = os.path.join(root, name)
            target = os.path.join(rootdir, relroot, name)
            #logger.info(f'applying project template at {target!r}')
            with open(source) as infile:
                template = infile.read()
            lines = []
            try:
                for line in template.splitlines():
                    lines.append(
                        line.format(**ns))
            except Exception as exc:
                raise Exception((f'problem applying template file {source!r} '
                                 f'({type(exc).__name__}: {exc})'))
            text = '\n'.join(lines)
            with open(target, 'w') as outfile:
                outfile.write(text)
