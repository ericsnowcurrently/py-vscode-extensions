
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
