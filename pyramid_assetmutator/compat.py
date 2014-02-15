# vim:fileencoding=utf-8:ai:ts=4:sts:et:sw=4:tw=80:
import sys

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

if PY3: # pragma: no cover
    string_types = str,
else: # pragma: no cover
    string_types = basestring,
