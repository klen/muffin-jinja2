import sys

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal  # py37

try:
    from cached_property import cached_property  # py37
except ImportError:
    from functools import cached_property  # py38
