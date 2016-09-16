================================================================================
Changelog
================================================================================


v0.4 -- 09/16/2016
================================================================================

* Fixed a bug where mutated files could be created with incorrect filenames if
  the ``each_boot`` setting was enabled with a ``remutate_check`` value of
  ``mtime`` or ``checksum``.
* Fixed a Windows bug due to ``shlex.split`` usage (thanks @tdamsma).
* Added a ``purge_mutated_path`` setting which can be used to remove all files
  from a specified ``mutated_path`` upon application boot.


v0.3 -- 04/10/2014
================================================================================

* Experimental support for template language parsing (e.g. you could use view
  helpers like ``request.route_url()`` in your CoffeeScript by installing the
  ``pyramid_jinja2`` package and using application.coffee.jinja2 as the asset
  source filename).


v0.2 -- 04/6/2014
================================================================================

* Experimental Py3k/pypy support.
* Tests added.
* Documentation updates.


v0.1 -- 02/15/2014
================================================================================

* Initial release.
