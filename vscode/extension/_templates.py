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
            source = os.path.join(root, name)
            target = os.path.join(rootdir, relroot, name)
            #logger.info(f'applying project template at {target!r}')
            with open(source) as infile:
                template = infile.read()
            text = template.format(**ns)
            with open(target, 'w') as outfile:
                outfile.write(text)
