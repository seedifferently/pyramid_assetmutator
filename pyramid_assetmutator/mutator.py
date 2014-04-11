# vim:fileencoding=utf-8:ai:ts=4:sts:et:sw=4:tw=80:
import os, re, glob, shlex, subprocess, hashlib
from pyramid.interfaces import IRendererFactory
from pyramid.path import AssetResolver
from pyramid.renderers import render

class Mutator(object):
    """
    Mutator class for the pyramid_assetmutator add-on.
    """
    def __init__(self, request, path, **kw):
        """
        Initialize the Mutator class.

        Required parameters:

        :type request: request
        :param request: The Pyramid application's current ``request``.

        :type path: string
        :param path: The Pyramid ``asset path``.

        Optional keyword parameters:

        :type mutator: dict or string
        :param mutator: Allows you to either specify a specific mutator to
                         use (e.g. ``coffee``), or assign a brand new
                         mutator dictionary to be used (e.g.
                         ``{'cmd': 'lessc', 'ext': 'css'}``)

        :type settings: dict
        :param settings: Explicitly pass your own settings dict, rather than
                         getting the settings from ``request.registry`` (usually
                         only used in combination with batch processing).

        :type registry: registry
        :param registry: Explicitly pass your own Pyramid ``registry`` (usually
                         only used in combination with batch processing).

        :type rendering_val: dict
        :param rendering_val: A dictionary that will be passed to the renderer
                              in the event that the path provided matches a
                              valid template renderer.

        :type batch: bool
        :param batch: Specify that the class should perform batch processing
                      rather than request-based processing.
        """
        self.request = request
        try:
            self.registry = kw['registry']
        except KeyError:
            self.registry = self.request.registry
        self.settings = kw.get('settings') or self.registry.settings
        self.path = path

        self.renderers = [
            key for key in \
            dict(self.registry.getUtilitiesFor(IRendererFactory)).keys() \
            if key not in ['json', 'string', '.txt']
        ]
        self.rendering_val = kw.get('rendering_val', {})

        self.mutators = self.settings.get('assetmutator.mutators')
        self.prefix = self.settings['assetmutator.asset_prefix']
        self.check_method = self.settings['assetmutator.remutate_check']
        self.mutated_path = self.settings['assetmutator.mutated_path']
        if self.mutated_path and not self.mutated_path.endswith(os.sep):
            self.mutated_path += os.sep
        self.mutator = kw.get('mutator')

        if (not self.mutators or not isinstance(self.mutators, dict)) and \
           not self.mutator:
            raise ValueError('No mutators were found.')

        self.batch = kw.get('batch', False)
        self.checksum = None
        self.mtime = None
        self.exists = False
        self.dest_dirpath = None
        self.parse_template = False

        if not self.batch:
            self._configure_paths()

    @property
    def mutated(self):
        """
        Property method to check and see if the initialized asset path has
        already been mutated.
        """
        self.exists = self.exists or self._check_exists(self.dest_fullpath)

        return self.exists

    def _configure_paths(self):
        """
        Checks/sets the various path settings needed for mutation.
        """

        # Parse source path
        self.src_fullpath = self._get_abspath(self.path)
        self.src_dirpath = os.path.dirname(self.src_fullpath)

        # Parse dest/mutated path (if specified)
        self.dest_dirpath = self._get_abspath(self.mutated_path or
                                              self.src_dirpath)

        # Setup various path variables
        if self.batch and not os.path.isdir(self.src_dirpath):
            raise EnvironmentError('Directory does not exist: %s' %
                                   self.src_dirpath)
        else:
            self.src_filename = os.path.basename(self.src_fullpath)
            self.src_name = os.path.splitext(self.src_filename)[0]

            if self.mutated_path and \
               os.path.splitext(self.src_filename)[-1] in self.renderers:
                # This asset uses a template renderer
                self.parse_template = True
                self.src_ext = os.path.splitext(self.src_name)[-1][1:]
                self.src_name = os.path.splitext(self.src_name)[0]
            else:
                self.src_ext = os.path.splitext(self.src_filename)[-1][1:]


            # Get/setup the mutator
            if self.mutator:
                if not isinstance(self.mutator, dict):
                    self.mutator = self.mutators.get(self.mutator, {})
            else:
                self.mutator = self.mutators.get(self.src_ext, {})

            # Make sure an appropriate mutator is defined
            if not self.mutator.get('cmd') or not self.mutator.get('ext'):
                raise ValueError('No mutator found for %s.' % self.src_ext)


            # Do various check/path settings
            dest_ext = self.mutator['ext']

            if self.check_method == 'exists':
                self.dest_filename = '%s%s.%s' % (self.prefix, self.src_name,
                                                  dest_ext)
            elif self.check_method == 'checksum':
                self.checksum = self.checksum or \
                                self._compute_checksum(self.src_fullpath)
                self.dest_filename = '%s%s.%s.%s' % (self.prefix, self.src_name,
                                                     self.checksum, dest_ext)
            else: # self.check_method == 'mtime'
                self.mtime = self.mtime or self._get_mtime(self.src_fullpath)
                self.dest_filename = '%s%s.%s.%s' % (self.prefix, self.src_name,
                                                     self.mtime, dest_ext)

            # Set the full destination/output path
            self.dest_fullpath = os.path.join(
                self.dest_dirpath,
                self.dest_filename
            )

            # Set the new assetpath to be returned to the template
            if not self.batch:
                if self.mutated_path:
                    self.new_path = self.mutated_path + self.dest_filename
                else:
                    self.new_path = re.sub(r'%s$' % self.src_filename,
                                                    self.dest_filename,
                                                    self.path)

    def _get_abspath(self, path):
        """
        Convenience method to compute the absolute path from an assetpath.
        """
        resolver = AssetResolver()

        if not os.path.isabs(path):
            # Try to resolve the asset full path
            path = resolver.resolve(path).abspath()

        return path

    def _compute_checksum(self, path):
        """
        Convenience method to compute the source's checksum for the mutated
        asset.
        """
        md5 = hashlib.md5()

        # Loop the file, adding chunks to the MD5 generator
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(128*md5.block_size), b''):
                md5.update(chunk)
        # Finally, add the mtime
        md5.update(str(os.path.getmtime(path)).encode('utf-8'))

        # Get the first 12 characters of the hexdigest
        self.checksum = md5.hexdigest()[:12]

        return self.checksum

    def _get_mtime(self, path):
        """
        Convenience method for getting the source's mtime for the mutated asset.
        """
        return os.path.getmtime(path)

    def _check_exists(self, path):
        """
        Convenience method to check if a file already exists.
        """
        if os.path.exists(path):
            return True
        else:
            return False

    def _process_template(self, source):
        """
        Renders a file using the specified renderer and returns the new source
        filename to use for the mutator.
        """
        self.src_filename = self.prefix + os.path.splitext(self.src_filename)[0]
        self.src_fullpath = os.path.join(self.dest_dirpath, self.src_filename)
        self.prefix = ''

        data = render(source, self.rendering_val, request=self.request)

        with open(self.src_fullpath, 'w') as f:
            f.write(data)

    def _run_mutator(self):
        """
        Runs the mutator for the initialized asset.
        """
        cmd = '%s %s' % (self.mutator['cmd'], self.src_fullpath)

        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        data, err = proc.communicate()

        if proc.returncode != 0 or err:
            raise EnvironmentError('%s\n\n%s' % (err, data))
        else:
            new_dirname = os.path.normpath(os.path.dirname(self.dest_fullpath))

            if not os.path.exists(new_dirname):
                os.makedirs(new_dirname)

            with open(self.dest_fullpath, 'wb') as f:
                f.write(data)

    def mutate(self):
        """
        Mutate the asset(s).
        """
        if self.batch == True:
            batch_path = self._get_abspath(self.path)

            for ext, config in self.mutators.items():
                for asset in glob.glob(os.path.join(batch_path, '*.%s' % ext)):
                    self.path = asset
                    self._configure_paths()
                    self._run_mutator()
        else:
            if not self.exists:
                if self.parse_template:
                    self._process_template(self.path)

                self._run_mutator()
                self.exists = True

            return self.new_path

    def mutated_data(self):
        """
        Return the mutated source of the initialized asset.
        """
        if not self.exists:
            raise ValueError('Source not found. Has it been mutated?')

        with open(self.dest_fullpath) as f:
            data = f.read()

        return data
