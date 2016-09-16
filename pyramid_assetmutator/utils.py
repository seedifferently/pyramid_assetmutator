import os
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
