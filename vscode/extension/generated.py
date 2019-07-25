import json
import os
import os.path
import shutil

from .. import util
from . import project, _templates


OUT_DIR = '.build'
#OUT_DIR = '.extension'


def generate(project=None, outdir=None, *,
             _project_from_raw=project.Info.from_raw,
             _abspath=os.path.abspath,
             _projfiles=None,
             _gen=None,
             ):
    """Produce all needed files to build an extension from the given root."""
    project = _project_from_raw(project)
    # No need to validate.
    if outdir:
        outdir = _abspath(outdir)
    else:
        outdir = os.path.join(project.root, OUT_DIR)
    if _projfiles is None:
        _projfiles = _get_project_files(project.root)
    return (_gen or _generate)(
            project.root,
            project.cfg,
            _projfiles,
            outdir,
            )


def _generate(root, cfg, projfiles, outdir, *,
             _mkdirs=os.makedirs,
             _apply_templates=_templates.apply_to_tree,
             _update_manifest=None,
             _copy_file=shutil.copyfile,
             _fix_manifest=(lambda c, o: _fix_manifest(c, o)),
             ):
    try:
        _mkdirs(outdir)
    except FileExistsError:
        pass
    _apply_templates('extension', outdir, cfg._asdict())
    (_update_manifest or _fix_manifest)(
            cfg,
            outdir,
            )

    # Copy over relevant project files.
    for name in projfiles:
        if not name[0].isupper():
            continue
        source = os.path.join(root, name)
        target = os.path.join(outdir, name)
        _copy_file(source, target)

    # Apply final fixes.
    _fix_manifest(cfg, outdir)


def _fix_manifest(cfg, outdir, *,
                  _editing=util.editing_json_file,
                  ):
    filename = os.path.join(outdir, 'package.json')
    with _editing(filename) as data:
        if cfg.author:
            author = {
                    'name': cfg.author.name,
                    }
            if cfg.author.email:
                author['email'] = cfg.author.email
            data['author'] = author


def _get_project_files(root, *,
                      _listdir=os.listdir,
                      ):
    names = []
    for name in _listdir(root):
        if not name[0].isupper():
            continue
        names.append(name)
    return names
