import configparser
import os.path
import re
import shutil
import subprocess

from .os import run_cmd


CONFIG = os.path.join('~', '.gitconfig')
GIT = shutil.which('git')

REMOTE_RE = re.compile(rf'''
    ^
    (\S+)  # <name>
    \s+
    (?:
        (?:
            git@
            (github.com)  # <provider>
            :
            ([^/]+)  # <user>
            /
            (.+?)  # <repo>
            [.]git
         )
        |
        (?:
            https://
            (github.com)  # <provider>
            /
            ([^/]+)  # <user>
            /
            (.+)  # <repo>
         )
     )
    \s+
    [(]
    (
        fetch
        |
        push
     )
    [)]
    $
''', re.VERBOSE)


def _git(*args, root='.'):
    argv = [GIT, *args]
    try:
        return run_cmd(argv)
    except Exception:
        if not os.path.exists(os.path.join(root, '.git', 'config')):
            return None
        raise  # re-raise


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


def _parse_remote(text):
    m = REMOTE_RE.match(text)
    if m is None:
        return (None,) * 5
    (name,
     g_provider, g_user, g_repo,
     h_provider, h_user, h_repo,
     kind,
     ) = m.groups()
    if g_provider:
        return name, kind, g_provider, g_user, g_repo
    else:
        return name, kind, h_provider, h_user, h_repo


def get_remote(root='.', name='origin'):
    """Return info for a remote in the given clone."""
    text = _git('remote', '-v')
    if text is None:
        return None
    for line in text.strip().splitlines():
        actual, kind, provider, user, repo = _parse_remote(uri)
        if actual != name:
            continue
        if kind != 'fetch':
            continue
        if not repo:
            continue
        return (provider, user, repo)
    return None


def get_repo_url(root='.' , *,
                     _get_remote=get_remote,
                     ):
    """Return the URL of the clone's origin."""
    remote = _get_remote(root, 'origin')
    if remote is None:
        return None
    provider, user, repp = remote
    return f'https://{provider}/{user}/{repo}'
