# vim:fileencoding=utf-8:ai:ts=4:sts:et:sw=4:tw=80:
try:
    from collections import OrderedDict
except ImportError:
    # Py 2.6 compat
    from ordereddict import OrderedDict

from pyramid.settings import asbool
from pyramid.events import ApplicationCreated, BeforeRender
from pyramid.threadlocal import get_current_request

from pyramid_assetmutator.utils import as_string, as_list
from pyramid_assetmutator.mutator import Mutator

SETTINGS_PREFIX = 'assetmutator.'

default_settings = (
    ('debug', asbool, 'false'),
    ('remutate_check', as_string, 'mtime'),
    ('asset_prefix', as_string, '_'),
    ('mutated_path', as_string, ''),
    ('each_request', asbool, 'true'),
    ('each_boot', asbool, 'false'),
    ('asset_paths', as_list, ('',)),
)

# Use an OrderedDict so that processing always happens in order
mutators = OrderedDict() # empty for now

def parse_settings(settings):
    parsed = {}
    def populate(name, convert, default):
        name = '%s%s' % (SETTINGS_PREFIX, name)
        value = convert(settings.get(name, default))
        parsed[name] = value
    for name, convert, default in default_settings:
        populate(name, convert, default)
    return parsed


def assign_assetmutator(config, ext, cmd, new_ext):
    """
    Configuration method to set up/assign an asset mutator. This allows the
    various ``assetmutator_*`` view helper methods to know which mutator to run
    for a specified asset path.
    
    :param ext: The file extension this mutator should match (e.g. coffee).
    :type ext: string - Required
    
    :param cmd: The command to run (e.g. coffee -c -p). The filename to be
                mutated will automatically be appended to the end of this
                string when running the command.
    :type cmd: string - Required
    
    :param new_ext: The extension that the mutated filename should have (e.g.
                    js).
    :type new_ext: string - Required
    
    
    .. warning:: The specified mutator command must be installed, must be
                 executable by the Pyramid process, and must *output the
                 mutated data to stdout*. The last point can get tricky
                 depending on the command, so be sure to check its command
                 switches for the appropriate option.
    
    For example, a mutator that would run ``.coffee`` files through the
    ``coffee`` command (compiling them into JavaScript) would look like::
    
        config.assign_assetmutator('coffee', 'coffee -c -p', 'js')
    """
    mutators[ext] = dict(cmd=cmd, ext=new_ext)

def assetmutator_url(path, **kw):
    """
    Returns a Pyramid :meth:`~pyramid.request.Request.static_url` of the mutated
    asset (and mutates the asset if needed).
    
    :param path: The Pyramid asset path to process.
    :type path: string - Required
    
    :type mutator: dict or string - Optional
    :param mutator: Allows you to override/specify a specific mutator to use
                     (e.g. ``coffee``), or assign a brand new mutator
                     dictionary to be used (e.g. ``{'cmd': 'lessc', 'ext':
                     'css'}``)
    """
    request = get_current_request()
    settings = request.registry.settings
    
    mutant = Mutator(settings, path, **kw)
    
    if not settings['assetmutator.each_request']:
        if not mutant.mutated:
            # TODO: Error?
            pass
        
        return request.static_url(mutant.new_path)
    else:
        if mutant.mutated:
            return request.static_url(mutant.new_path)
        else:
            return request.static_url(mutant.process())


def assetmutator_path(path, **kw):
    """
    Returns a Pyramid :meth:`~pyramid.request.Request.static_path` of the
    mutated asset (and mutates the asset if needed).
    
    :param path: The Pyramid asset path to process.
    :type path: string - Required
    
    :type mutator: dict or string - Optional
    :param mutator: Allows you to override/specify a specific mutator to use
                     (e.g. ``coffee``), or assign a brand new mutator
                     dictionary to be used (e.g. ``{'cmd': 'lessc', 'ext':
                     'css'}``)
    """
    request = get_current_request()
    settings = request.registry.settings
    
    mutant = Mutator(settings, path, **kw)
    
    if not settings['assetmutator.each_request']:
        if not mutant.mutated:
            # TODO: Error?
            pass
        
        return request.static_path(mutant.new_path)
    else:
        if mutant.mutated:
            return request.static_path(mutant.new_path)
        else:
            return request.static_path(mutant.process())

def assetmutator_source(path, **kw):
    """
    Returns the source data/contents of the mutated asset (and mutates the
    asset if needed). This is useful when you want to output inline data (e.g.
    for inline JavaScript blocks).
    
    :param path: The Pyramid asset path to process.
    :type path: string - Required
    
    :type mutator: dict or string - Optional
    :param mutator: Allows you to override/specify a specific mutator to use
                     (e.g. ``coffee``), or assign a brand new mutator
                     dictionary to be used (e.g. ``{'cmd': 'lessc', 'ext':
                     'css'}``)
    
    .. note:: Many template packages escape output by default. Consult your
              template language's syntax to output an unescaped string.
    """
    request = get_current_request()
    settings = request.registry.settings
    
    mutant = Mutator(settings, path, **kw)
    
    if not settings['assetmutator.each_request']:
        if not mutant.mutated:
            # TODO: Error?
            return None
        
        return mutant.mutated_data()
    else:
        if mutant.mutated:
            return mutant.mutated_data()
        else:
            mutant.process()
            return mutant.mutated_data()

def assetmutator_assetpath(path, **kw):
    """
    Returns a Pyramid `asset specification`_ such as
    ``pkg:static/path/to/file.ext`` (and mutates the asset if needed).
    
    :param path: The Pyramid asset path to process.
    :type path: string - Required
    
    :type mutator: dict or string - Optional
    :param mutator: Allows you to override/specify a specific mutator to use
                     (e.g. ``coffee``), or assign a brand new mutator
                     dictionary to be used (e.g. ``{'cmd': 'lessc', 'ext':
                     'css'}``)
    
    This function could be used to nest ``pyramid_assetmutator`` calls. e.g.
    ``assetmutator_path(assetmutator_assetpath('pkg:static/js/script.coffee'))``
    could compile a CoffeeScript file into JS, and then further minify the JS
    file if your mutator configuration looked something like::
    
        config.assign_assetmutator('coffee', 'coffee -c -p', 'js')
        config.assign_assetmutator('js', 'uglifyjs', 'js')
    
    .. _asset specification: http://pyramid.readthedocs.org/en/latest/
                             glossary.html#term-asset-specification
    """
    request = get_current_request()
    settings = request.registry.settings
    
    mutant = Mutator(settings, path, **kw)
    
    if not settings['assetmutator.each_request']:
        if not mutant.mutated:
            # log an error
            pass
        
        return mutant.new_path
    else:
        if mutant.mutated:
            return mutant.new_path
        else:
            return mutant.process()


def applicationcreated_subscriber(event):
    settings = event.app.registry.settings
    settings['assetmutator.mutators'] = mutators
    
    if settings['assetmutator.each_boot']:
        asset_paths = settings['assetmutator.asset_paths']
        
        for asset_path in asset_paths:
            mutator = Mutator(settings, asset_path, batch=True)
            mutator.batch_process()

def beforerender_subscriber(event):
    event['assetmutator_url'] = assetmutator_url
    event['assetmutator_path'] = assetmutator_path
    event['assetmutator_source'] = assetmutator_source
    event['assetmutator_assetpath'] = assetmutator_assetpath

def includeme(config):
    """
    Activate the package; typically called via
    ``config.include('pyramid_assetmutator')`` instead of being invoked
    directly.
    """
    settings = parse_settings(config.registry.settings)
    config.registry.settings.update(settings)
    
    config.add_directive('assign_assetmutator', assign_assetmutator)
    config.add_subscriber(applicationcreated_subscriber, ApplicationCreated)
    config.add_subscriber(beforerender_subscriber, BeforeRender)
