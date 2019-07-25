import contextlib
import json


@contextlib.contextmanager
def editing_file(jsonfile, *,
                 _open=open,
                 _edit=(lambda f: _edit_file(f)),
                 ):
    """A context manager to load JSON from a file and write back when done."""
    if isinstance(jsonfile, str):
        filename = jsonfile
        with _open(filename, 'r+') as jsonfile:
            yield from _editing_file(jsonfile)
    else:
        yield from _editing_file(jsonfile)


def _editing_file(jsonfile, *,
                  _load=json.load,
                  _dump=json.dump,
                  ):
    data = _load(jsonfile)
    yield data
    jsonfile.seek(0)
    _dump(data, jsonfile, indent='    ')


#def _editing_file(jsonfile, *,
#                  _read_all=read_all,
#                  _write_all=write_all,
#                  _loads=json.loads,
#                  _dumps=json.dumps,
#                  ):
#    text = _read_all(jsonfile)
#    data = _loads(text)
#    yield data
#    text = _dumps(data)
#    # XXX Worry about races?
#    _write_all(filename, text)
