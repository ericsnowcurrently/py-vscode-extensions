import configparser
import os.path


CONFIG = os.path.join('~', '.gitconfig')


def get_config(cfgfile=None, *,
               _expand_user=os.path.expanduser,
               _open=open,
               _new_ini=configparser.ConfigParser,
               ):
    """Return a ConfigParser object for the give config.

    Return None if it is missing.
    """
    if cfgfile is None or cfgfile == '':
        cfgfile = _expand_user(CONFIG)
    if isinstance(cfgfile, str):
        with _open(cfgfile) as cfgfile:
            return get_config(cfgfile)

    ini = _new_ini()
    ini.read_file(cfgfile)
    return ini


def get_committer(ini=None, *,
                  _get_config=get_config,
                  ):
    """Return the combined "person" string based on the user git config."""
    if ini is None:
        ini = _get_config()

    name = email = None
    try:
        name = ini['user']['name']
        email = ini['user']['email']
    except KeyError:
        pass
    if not name:
        return None
    return f'{name} <{email}>' if email else name
