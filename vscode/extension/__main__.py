import argparse
import sys


#######################################
# the script

def parse_args(prog=sys.argv[0], argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
            prog=prog,
            )
    parser.add_argument('--show-traceback', dest='showtb', action='store_true')

    args = parser.parse_args(argv)
    ns = vars(args)

    cmd = ns.pop('cmd', None)

    showtb = ns.pop('showtb')

    return showtb, cmd, ns


def main(cmd):
    raise NotImplementedError


if __name__ == '__main__':
    showtb, cmd, kwargs = parse_args()
    try:
        main(cmd, **kwargs)
    except Exception as exc:
        if showtb:
            raise
        sys.exit(f'ERROR: {exc}')
