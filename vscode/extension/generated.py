import os
import os.path
import shutil

from . import project, _templates


OUT_DIR = '.build'
#OUT_DIR = '.extension'


def generate(root=None, outdir=None, *,
             _cwd=os.getcwd(),
             _abspath=os.path.abspath,
             _cfg_from_file=project.Config.from_file,
             _apply_templates=_templates.apply,
             _mkdirs=os.makedirs,
             _listdir=os.listdir,
             _copy_file=shutil.copyfile,
             ):
    """Produce all needed files to build an extension from the given root."""
    if not root:
        root = _cwd
    files = project.Files(root)
    # No need to validate.
    if outdir:
        outdir = _abspath(outdir)
    else:
        outdir = os.path.join(files.root, OUT_DIR)
    cfg = _cfg_from_file(files.cfgfile)
    # No need to validate.

    # Create the files and directories.
    try:
        _mkdirs(outdir)
    except FileExistsError:
        pass
    _apply_templates('extension', outdir, cfg._asdict())
    for name in _listdir(files.root):
        if not name[0].isupper():
            continue
        source = os.path.join(files.root, name)
        target = os.path.join(outdir, name)
        _copy_file(source, target)
    # XXX Fix package.json.
