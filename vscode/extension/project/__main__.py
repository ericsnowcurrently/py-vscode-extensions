import argparse
import os
import os.path
import sys

from . import lifecycle, info


def cmd_init(root=None, *,
             _init=lifecycle.initialize,
             **kwargs
             ):
    cfg = info.Config(**kwargs)
    cfg.validate()
    _init(cfg, root)


def cmd_generate(root=None, outdir=None, *,
                 _generate=lifecycle.generate_extension,
                 **kwargs
                 ):
    _generate(root, outdir, **kwargs)


#######################################
# the script

COMMANDS = {
        'init': cmd_init,
        'generate': cmd_generate,
        }


def get_env_var(name, default=None, *,
                _env_get=(lambda *args: os.environ.get(*args)),
                ):
    return _env_get(f'PYVSC_{name}', default)


def get_env_flag(name, *,
                 _get_env_var=get_env_var,
                 ):
    value = (_get_env_var(name) or '').strip()
    if value.lower() in ('', '0', 'f', 'false'):
        return False
    return True


def parse_args(prog=sys.argv[0], argv=sys.argv[1:], *,
               _get_env_flag=get_env_flag,
               ):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--show-traceback', dest='showtb',
                        action='store_true', default=None)
    common.add_argument('--no-show-traceback', dest='showtb',
                        action='store_false', default=None)

    parser = argparse.ArgumentParser(
            prog=prog,
            parents=[common],
            )
    subs = parser.add_subparsers(dest='cmd')

    init = subs.add_parser('init', parents=[common])
    init.add_argument('--name')
    # XXX version
    # XXX minvscode
    # XXX license
    # XXX author
    init.add_argument('root')

    generate = subs.add_parser('generate', parents=[common])
    generate.add_argument('--outdir')
    generate.add_argument('root')

    args = parser.parse_args(argv)
    ns = vars(args)

    cmd = ns.pop('cmd')
    if not cmd:
        parser.error('missing command')

    showtb = ns.pop('showtb')
    if showtb is None:
        showtb = _get_env_flag('SHOW_TRACEBACK')

    args.root = args.root or '.'

    if cmd == 'init':
        if not args.name:
            if args.root == '.' or args.root.endswith(os.path.sep):
                parser.error('missing project name')
            args.name = os.path.basename(args.root)

    return showtb, cmd, ns


def main(cmd, *,
         _commands=COMMANDS,
         **kwargs
         ):
    if not cmd:
        raise TypeError('missing cmd')
    try:
        run_cmd = _commands[cmd]
    except KeyError:
        raise ValueError(f'unsupported cmd {cmd!r}')

    run_cmd(**kwargs)


if __name__ == '__main__':
    showtb, cmd, kwargs = parse_args()
    try:
        main(cmd, **kwargs)
    except Exception as exc:
        if showtb:
            raise
        msg = str(exc)
        if not msg:
            msg = type(exc).__name__
        sys.exit(f'ERROR: {msg}')
