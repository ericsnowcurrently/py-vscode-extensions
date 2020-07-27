from vscode.util.scriptutil import configure_logger
from vscode.extension.project.__main__ import logger, parse_args, main


cmd, kwargs, verbosity, logfile, traceback_cm = parse_args()
configure_logger(logger, verbosity, logfile=logfile)
with traceback_cm:
    main(cmd, **kwargs)
