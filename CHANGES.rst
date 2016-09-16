Latest Changes
================================================================================


v0.4 -- 09/16/2016
--------------------------------------------------------------------------------

* Fixed a bug where mutated files could be created with incorrect filenames if
  the ``each_boot`` setting was enabled with a ``remutate_check`` value of
  ``mtime`` or ``checksum``.
* Fixed a Windows bug due to ``shlex.split`` usage (thanks @tdamsma).
* Added a ``purge_mutated_path`` setting which can be used to remove all files
  from a specified ``mutated_path`` upon application boot.
