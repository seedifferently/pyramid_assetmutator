import os
import hashlib
from pyramid.path import AssetResolver
from pyramid_assetmutator.compat import string_types

def as_string(value):
    result = ''
    if isinstance(value, string_types):
        result = value.strip()
    return result

def as_cr_separated_list(value):
    if isinstance(value, string_types):
        value = filter(None, [x.strip() for x in value.splitlines()])
    return value

def as_list(value):
    values = as_cr_separated_list(value)
    result = []
    for value in values:
        subvalues = value.split()
        result.extend(subvalues)
    return result

def get_abspath(path):
    """
    Convenience method to compute the absolute path from an assetpath.
    """
    resolver = AssetResolver()

    if not os.path.isabs(path):
        # Try to resolve the asset full path
        path = resolver.resolve(path).abspath()

    return path

def get_stat(path):
    """
    Convenience method for getting the size and mtime for the specified
    ``path``.
    """
    statinfo = os.stat(path)

    return '%s.%s' % (statinfo.st_size, statinfo.st_mtime)

def hexhashify(string):
    """
    Return a :func:`hex` value of the :func:`hash` of the passed ``string``.
    """
    return hex(hash(string))

def compute_md5(path):
    """
    Convenience method to compute the source's MD5 checksum for the specified
    ``path``.
    """
    md5 = hashlib.md5()

    # Loop the file, adding chunks to the MD5 generator
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(128*md5.block_size), b''):
            md5.update(chunk)

    # The first 12 characters of the hexdigest should be plenty
    return md5.hexdigest()[:12]
