================================================================================
Changelog
================================================================================


v1.0b1 -- 2/22/2017
================================================================================

* Added an ``always_remutate`` setting which provides the ability to specify
  assets that should *always* be remutated (even if a source file change was not
  detected).
* Tweaked the output filename format for mutated files. The new format should be
  significantly more resistant to edge-case naming collisions when utilizing a
  ``remutate_check`` of ``exists``.
* Renamed the (default) ``mtime`` value for the ``remutate_check`` setting to
  ``stat``. It now checks both the size and last modified time of the asset
  source file.
* The ``asset_paths`` setting has been merged into the ``each_boot`` setting.
  Now instead of receiving a boolean, ``each_boot`` must receive a list
  specifying assets that should be checked/mutated when the application boots.
* Renamed the ``asset_prefix`` setting to ``mutated_file_prefix`` in an effort
  to be more explicit.


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
