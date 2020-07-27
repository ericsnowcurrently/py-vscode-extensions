import logging
import os
import os.path
import sys

from . import lifecycle, info


logger = logging.getLogger(__name__)


def _new_config(**kwargs):
    cfg = info.Config(**kwargs)
    cfg.validate()
    return cfg


#######################################
# commands

def cmd_init(root=None, *,
             _new_config=_new_config,
             _init=lifecycle.initialize,
             **kwargs
             ):
    logger.info(f'seting up the project at {root or "."} ...')
    cfg = _new_config(**kwargs)
    _init(cfg, root)
    logger.info('done!')


def cmd_generate(root=None, outdir=None, *,
                 _generate=lifecycle.generate_extension,
                 **kwargs
                 ):
    logger.info(f'generating the extension in {root or "."}/build/ ...')
    _generate(root, outdir, **kwargs)
    logger.info('done!')


COMMANDS = {
    'init': cmd_init,
    'generate': cmd_generate,
}


#######################################
# the script

def parse_args(prog=sys.argv[0], argv=sys.argv[1:]):
    import argparse
    from vscode.util.scriptutil import (
        add_verbosity_cli,
        add_logging_cli,
        add_traceback_cli,
    )

    common = argparse.ArgumentParser(add_help=False)
    process_verbosity = add_verbosity_cli(common)
    process_logging = add_logging_cli(common)
    process_tb = add_traceback_cli(common)

    parser = argparse.ArgumentParser(
        prog=prog,
        parents=[common],
    )
    subs = parser.add_subparsers(dest='cmd')

    sub_init = subs.add_parser('init',
                               parents=[common],
                               description='Set up the project (add setup.py, setup.cfg, etc.)',
                               )
    sub_init.add_argument('--name')
    # XXX version
    # XXX minvscode
    # XXX license
    # XXX author
    sub_init.add_argument('root')

    sub_generate = subs.add_parser('generate',
                                   parents=[common],
                                   description='Produce the extension code for the project (in the "build" directory)',
                                   )
    sub_generate.add_argument('--outdir')
    sub_generate.add_argument('root')

    args = parser.parse_args(argv)
    ns = vars(args)

    verbosity = process_verbosity(args)
    logfile = process_logging(args)
    traceback_cm = process_tb(args)

    cmd = ns.pop('cmd')
    if not cmd:
        parser.error('missing command')

    args.root = args.root or '.'

    if cmd == 'init':
        if not args.name:
            if args.root == '.' or args.root.endswith(os.path.sep):
                parser.error('missing project name')
            args.name = os.path.basename(args.root)

    return cmd, ns, verbosity, logfile, traceback_cm


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
    from vscode.util.scriptutil import configure_logger
    cmd, kwargs, verbosity, logfile, traceback_cm = parse_args()
    configure_logger(logger, verbosity, logfile=logfile)
    with traceback_cm:
        main(cmd, **kwargs)
