import os.path


EXT_ROOT = os.path.dirname(__file__)
TEMPLATES = os.path.join(EXT_ROOT, '.templates')


# Clean up the namespace.
del os
