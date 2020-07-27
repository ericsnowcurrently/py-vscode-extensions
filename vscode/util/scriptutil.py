import contextlib
import logging
import os
import sys


def get_env_flag(name, *,
                 _get_env_var=(lambda *args: os.environ.get(*args)),
                 ):
    value = (_get_env_var(name) or '').strip()
    if value.lower() in ('', '0', 'f', 'false'):
        return False
    return True


##################################
# CLI helpers

TRACEBACK = get_env_flag('SHOW_TRACEBACK')
VERBOSITY = 3


def add_logging_cli(parser):
    parser.add_argument('--logfile')

    def process_args(args):
        ns = vars(args)
        return ns.pop('logfile')
    return process_args


def add_verbosity_cli(parser, *, default=VERBOSITY):
    parser.add_argument('-q', '--quiet', action='count', default=0)
    parser.add_argument('-v', '--verbose', action='count', default=0)

    def process_args(args):
        ns = vars(args)
        verbosity = max(0, default + ns.pop('verbose') - ns.pop('quiet'))
        return verbosity
    return process_args


def add_traceback_cli(parser, *, default=TRACEBACK):
    parser.add_argument('--traceback', '--tb', action='store_true',
                        default=default)
    parser.add_argument('--no-traceback', '--no-tb', dest='traceback',
                        action='store_const', const=False)

    def process_args(args):
        ns = vars(args)
        showtb = ns.pop('traceback')

        @contextlib.contextmanager
        def traceback_cm():
            try:
                yield
            except BrokenPipeError:
                # It was piped to "head" or something similar.
                pass
            except Exception as exc:
                if not showtb:
                    sys.exit(f'ERROR: {exc}')
                raise  # re-raise
            except KeyboardInterrupt:
                if not showtb:
                    sys.exit('\nINTERRUPTED')
                raise  # re-raise
            except BaseException as exc:
                if not showtb:
                    sys.exit(f'{type(exc).__name__}: {exc}')
                raise  # re-raise
        return traceback_cm()
    return process_args


##################################
# tables

def generate_table(cols):
    header = []
    div = []
    fmt = []
    for name, width in cols.items():
        #header.append(f'{:^%d}' % (width,))
        header.append(name.center(width + 2))
        div.append('-' * (width + 2))
        fmt.append(' {:%s} ' % (width,))
    return ' '.join(header), ' '.join(div), ' '.join(fmt)


def format_table(rows, cols, *, show_total=True, fit=True):
    header, div, fmt = generate_table(cols)
    yield header
    yield div
    total = 0
    if fit:
        widths = [w for w in cols.values()][:-1]
        for total, row in enumerate(rows):
            fixed = (str(v)[:w] for v, w in zip(row, widths))
            yield fmt.format(*fixed, *row[-1:])
    else:
        for total, row in enumerate(rows):
            yield fmt.format(*row)
    yield div
    if show_total:
        yield ''
        yield f'total: {total}'


##################################
# logging

def configure_logger(logger, verbosity=VERBOSITY, *,
                     logfile=None,
                     maxlevel=logging.CRITICAL,
                     ):
    level = max(1,  # 0 disables it, so we use the next lowest.
                min(maxlevel,
                    maxlevel - verbosity * 10))
    logger.setLevel(level)
    #logger.propagate = False

    if not logger.handlers:
        if logfile:
            handler = logging.FileHandler(logfile)
        else:
            handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        #handler.setFormatter(logging.Formatter())
        logger.addHandler(handler)
