import os.path


def resolve(filename, *,
            _expand_vars=os.path.expandvars,
            _expand_user=os.path.expanduser,
            _abspath=os.path.abspath,
            ):
    """Return the absolute path of the given filename."""
    return _abspath(
        _expand_user(
            _expand_vars(filename or '.')))


def read_all(filename, *,
             _open=open,
             ):
    """Return the text contents of the given file."""
    with _open(filename, 'r') as infile:
        return infile.read()


def write_all(filename, text, *,
              _open=open,
              ):
    """Write the given text to the file."""
    with _open(filename, 'w') as outfile:
        return outfile.write(text)
