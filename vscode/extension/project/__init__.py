import os.path


DATA_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(DATA_DIR, '.templates')


# Pull in exported names.
from .info import (
        Config,
        Files,
        Project,
        )
from .lifecycle import (
        initialize,
        generate_extension,
        )


# Clean up the namespace.
del os
