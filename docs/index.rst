pyramid_assetmutator
====================

Overview
--------

``pyramid_assetmutator`` provides simple and dynamic asset mutation (also known
as compiling or piping) for your Pyramid_ applications.

Inspired by other more powerful asset management packages, its goal is to
provide a basic and straightforward mechanism for asset *compilation* (e.g.
CoffeeScript/LESS), *minification* (e.g. jsmin), and *optimization* (e.g.
pngcrush).

As of version 0.3, it also adds experimental support for template language
parsing (e.g. you could use view helpers like `request.route_url()` in your
CoffeeScript by installing the `pyramid_jinja2` package and using
application.js.coffee.jinja2 as the asset source filename).

.. warning:: This package only supports Pyramid 1.3 or later.

.. _Pyramid: http://www.pylonsproject.org/


Installation
------------

To install, simply::

    pip install pyramid_assetmutator

* You'll need to have `Python`_ 2.6+ and `pip`_ installed.

.. _Python: http://www.python.org
.. _pip: http://www.pip-installer.org


Setup
-----

Once ``pyramid_assetmutator`` is installed, you must include it in your Pyramid
project's configuration. This is typically done using Pyramid's
:meth:`config.include <pyramid.config.Configurator.include>` mechanism in your
project's ``__init__.py``:

.. code-block:: python

    config = Configurator(...)
    config.include('pyramid_assetmutator')

Next, you must assign one or more *mutators* via the newly injected
:meth:`~pyramid_assetmutator.assign_assetmutator` configuration method, so that
your application can know what kind of assets you'll be asking it to mutate. The
configuration syntax for your Pyramid project's ``__init__.py`` is::

    config.assign_assetmutator('SOURCE EXTENSION', 'COMMAND', 'OUTPUT EXTENSION')

For example, the following configuration would activate ``pyramid_assetmutator``
in your app, and initialize mutators for CoffeeScript and LESS files (allowing
them to be compiled into the appropriate JavaScript and CSS):

.. code-block:: python

    config = Configurator(...)
    config.include('pyramid_assetmutator')
    config.assign_assetmutator('coffee', 'coffee -c -p', 'js')
    config.assign_assetmutator('less', 'lessc', 'css')


Usage
-----

Once you have included the module and configured your mutators, you will then be
able to call one of the following view helper methods in your templates to
*reference* (with Pyramid's `asset specification`_ syntax) and *"mutate"* (if
needed) an asset:

.. automodule:: pyramid_assetmutator
  :noindex:

.. autoclass:: AssetMutator
  :noindex:
  :members:

.. _asset specification: http://pyramid.readthedocs.org/en/latest/glossary.html#term-asset-specification


Template Language Parsing
~~~~~~~~~~~~~~~~~~~~~~~~~

In version 0.3, experimental support for template language parsing was added. As
long as the template language is known to Pyramid (e.g. one of `these bindings`_
has been configured), you can append the expected template filename extension to
your asset filename and it will attempt to parse it before mutation.

For example, if the `pyramid_jinja2` package was configured, you could specify
an asset path to an asset named `application.coffee.jinja2` and
`pyramid_assetmutator` would run it through the Jinja2 renderer before mutation.

.. warning:: Current support is experimental, and there are a few caveats:

  1. You must specify a `mutated_path` in your configuration so that the
     intermediate-step sources can be stored and parsed from that directory.
  2. Template parsing is currently only supported when using the `each_request`
     configuration (which is the default configuration).
  3. Hopefully obvious, but if the asset you are parsing uses a syntax that
     conflicts with the tempate language's syntax, things probably won't work
     out very well for you.

.. _these bindings: https://pyramid.readthedocs.org/en/latest/narr/templates.html#available-add-on-template-system-bindings


Examples
~~~~~~~~

An example using the Chameleon_ template language (and assuming that a mutator
has been assigned for "coffee" files):

.. code-block:: xml

    <script src="${assetmutator_url('pkg:static/js/test.coffee')}"
            type="text/javascript"></script>

And now the same example, but for ``inline`` code output:

.. code-block:: xml

    <script type="text/javascript">
    ${structure: assetmutator_source('pkg:static/js/test.coffee')}
    </script>

Or, if your default JS mutator configuration uses ``jsmin``, but you wanted to
use ``uglifyjs`` for a particular asset:

.. code-block:: xml

    <script src="${assetmutator_url('pkg:static/js/test.js', mutator={'cmd': 'uglifyjs', 'ext': 'js'})}"
            type="text/javascript"></script>

As of version 0.3, your asset source could be parsed with Chameleon as well:

.. code-block:: xml

    <script src="${assetmutator_url('pkg:static/js/test.coffee.pt')}"
            type="text/javascript"></script>

Lastly, :meth:`~pyramid_assetmutator.assetmutator_assetpath` is a particularly
nifty/dirty method which gives you the ability to chain mutators. For example,
if you wanted to mutate a CoffeeScript file into a JavaScript file and then
minify the JavaScript file, you could do something like:

.. code-block:: xml

    <script src="${assetmutator_url(assetmutator_assetpath('pkg:static/js/test.coffee'))}"
            type="text/javascript"></script>

.. _Chameleon: http://chameleon.repoze.org/


Mutators
--------

You can assign as many mutators as you like using the
``config.assign_assetmutator`` method, but it is important to keep in mind the
following:

    * The mutator ``COMMAND`` must be installed, must be executable by the
      Pyramid process, and by default must *output the mutated data to stdout*.
      The last point can get tricky depending on the command, so be sure to
      check its command switches for the appropriate option (or create a wrapper
      as seen below).
    * Mutators are executed in order (first in, first out), which means that it
      is possible to compile a CoffeeScript file into a JavaScript file and then
      minify the JavaScript file; but for certain configuations this may only
      work if you have assigned the CoffeeScript compiler before the JavaScript
      minifier.

Here are a few mutator commands that have been tested and are known to work as
of this writing:

.. code-block:: python

    # CoffeeScript - http://coffeescript.org/
    config.assign_assetmutator('coffee', 'coffee -c -p', 'js')

    # Dart - http://www.dartlang.org/
    # Requires a wrapper - http://gist.github.com/98aa5e3f3d183d908caa
    config.assign_assetmutator('dart', 'dart_wrapper', 'js')

    # TypeScript - http://www.typescriptlang.org/
    # Requires a wrapper - http://gist.github.com/eaace8a89881c8ca9cda
    config.assign_assetmutator('ts', 'tsc_wrapper', 'js')

    # LESS - http://lesscss.org/
    config.assign_assetmutator('less', 'lessc', 'css')

    # SASS/SCSS - http://sass-lang.com/
    config.assign_assetmutator('sass', 'sass', 'css')
    config.assign_assetmutator('scss', 'sass --scss', 'css')

    # jsmin - http://www.crockford.com/javascript/jsmin.html
    config.assign_assetmutator('js', 'jsmin', 'js')

    # UglifyJS - http://github.com/mishoo/UglifyJS
    config.assign_assetmutator('js', 'uglifyjs', 'js')

    # pngcrush - http://pmt.sourceforge.net/pngcrush/
    # Requires a wrapper - http://gist.github.com/3a0c72ef9bb217315347
    config.assign_assetmutator('png', 'pngcrush_wrapper', 'png')


Settings
--------

Additional settings are configurable via your Pyramid application's ``.ini``
file (in the app section representing your Pyramid app) using the
``assetmutator`` key:

    ``assetmutator.remutate_check``
        :Default: mtime
        :Options: exists | mtime | checksum

        Specifies what type of method to use for checking to see if an asset
        source has been updated and should be re-mutated. If set to ``exists``
        (fastest, but not usually ideal), then it will only check to see if a
        filename matching the mutated version of the asset already exists.
        If set to ``mtime``, then only the last modified time will be checked.
        If set to ``checksum`` (slowest, but most reliable), then the file
        contents will be checked.

    ``assetmutator.asset_prefix``
        :Default: _

        A prefix to add to the mutated asset filename.

    ``assetmutator.mutated_path``
        :Default: None

        By default, mutated files are stored in the same directory as their
        source files. If you would like to have all mutated files stored in a
        specific directory, you can define a Pyramid asset specification here
        (e.g. ``pkg:static/cache/``).

        .. note:: The specified path must be a valid `asset specification`_ that
                  matches a configured `static view`_, and must be writable by
                  the application.

    ``assetmutator.each_request``
        :Default: true

        Whether or not assets should be checked/mutated during each request
        when the template language encounters one of the ``assetmutator_*``
        methods.

    ``assetmutator.each_boot``
        :Default: false

        Whether or not assets should be checked/mutated when the application
        boots (uses Pyramid's :class:`~pyramid.events.ApplicationCreated`
        event).

        .. note:: If set to true, then you must specify the ``asset_paths`` to
                  be checked (see below).

    ``assetmutator.asset_paths``
        :Default: None

        Which path(s) should be checked/mutated when the application boots
        (only loaded if ``assetmutator.each_boot`` is set to true).

        .. note:: Asset path checks are not recursive, so you must explicitly
                  specify each path that you want checked.

For example, if you wanted to only check/mutate assets on each boot (a good
practice for production environments), and only wanted to process the ``js``
and ``css`` directories, and would like each mutated ``_filename`` to be saved
in a ``myapp:static/cache/`` directory, then your ``.ini`` file could look
something like:

.. code-block:: ini

    [app:main]
    ...other settings...
    assetmutator.mutated_path = myapp:static/cache/
    assetmutator.each_request = false
    assetmutator.each_boot = true
    assetmutator.asset_paths =
        myapp:static/js
        myapp:static/css

.. _asset specification: http://pyramid.readthedocs.org/en/latest/glossary.html#term-asset-specification
.. _static view: http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html


Asset Concatenation (a.k.a Asset Pipeline)
------------------------------------------

A feature that is popular in some web frameworks (e.g. Ruby on Rails) is the
ability to combine all assets that share a common type into a single file for
sourcing within your views. Unfortunately, this functionality is currently
beyond the scope of ``pyramid_assetmutator``. Please have a look at the
pyramid_fantastic_ and pyramid_webassets_ packages instead.

.. _pyramid_fantastic: http://github.com/FormAlchemy/pyramid_fanstatic
.. _pyramid_webassets: http://github.com/sontek/pyramid_webassets


More Information
----------------

.. toctree::
   :maxdepth: 1

   api.rst


Development Versions / Reporting Issues
---------------------------------------

Visit http://github.com/seedifferently/pyramid_assetmutator to download
development or tagged versions.

Visit http://github.com/seedifferently/pyramid_assetmutator/issues to report
issues.


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
