Latest Changes
================================================================================


v1.0b1 -- 2/22/2017
--------------------------------------------------------------------------------

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
