import argparse
import sys

from . import project, generated


def cmd_init(root=None, *,
             _init=project.initialize,
             **kwargs
             ):
    cfg = project.Config(**kwargs)
    cfg.validate()
    _init(cfg, root)


def cmd_generate(root=None, outdir=None, *,
                 _generate=generated.generate,
                 **kwargs
                 ):
    _generate(root, outdir, **kwargs)


#######################################
# the script

COMMANDS = {
        'init': cmd_init,
        'generate': cmd_generate,
        }


def parse_args(prog=sys.argv[0], argv=sys.argv[1:]):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--show-traceback', dest='showtb', action='store_true')

    parser = argparse.ArgumentParser(
            prog=prog,
            parents=[common],
            )
    subs = parser.add_subparsers(dest='cmd')

    init = subs.add_parser('init', parents=[common])
    init.add_argument('--root')
    # XXX version
    # XXX minvscode
    # XXX license
    # XXX author
    init.add_argument('name')

    generate = subs.add_parser('generate', parents=[common])
    generate.add_argument('--root')
    generate.add_argument('--outdir')

    args = parser.parse_args(argv)
    ns = vars(args)

    cmd = ns.pop('cmd')
    if not cmd:
        parser.error('missing command')

    showtb = ns.pop('showtb')

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
