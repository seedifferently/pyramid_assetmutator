import os
import re
import glob
import shlex
import subprocess
from fnmatch import fnmatch
from pyramid.interfaces import IRendererFactory
from pyramid.renderers import render
from pyramid_assetmutator.utils import get_abspath, get_stat, hexhashify, \
                                       compute_md5


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
        self.prefix = self.settings['assetmutator.mutated_file_prefix']
        self.check_method = self.settings['assetmutator.remutate_check']
        self.mutated_path = self.settings['assetmutator.mutated_path']
        self.always_remutate = self.settings['assetmutator.always_remutate']

        if self.mutated_path and not self.mutated_path.endswith(os.sep):
            self.mutated_path += os.sep
        self.mutator = kw.get('mutator')

        if (not self.mutators or not isinstance(self.mutators, dict)) and \
           not self.mutator:
            raise RuntimeError('No mutators were found.')

        self.batch = kw.get('batch', False)
        self.checksum = None
        self.stat = None
        self.exists = False
        self.dest_dirpath = None
        self.parse_template = False

        if not self.batch:
            self._configure_paths()

    @property
    def is_mutated(self):
        """
        Property method to check and see if the initialized asset path has
        already been mutated.
        """
        self.exists = self.exists or os.path.exists(self.dest_fullpath)

        return self.exists

    @property
    def should_mutate(self):
        """
        Checks if a ``mutant`` object should be [re]mutated.
        """
        if self.is_mutated is not True:
            return True

        if self.always_remutate:
            if '*' in self.always_remutate or self.path in self.always_remutate:
                return True
            else:
                for val in self.always_remutate:
                    if fnmatch(self.path, val):
                        return True

        return False

    def _configure_paths(self):
        """
        Checks/sets the various path settings needed for mutation.
        """
        # Setup various path variables
        self.src_fullpath = get_abspath(self.path)
        self.src_dirpath = os.path.dirname(self.src_fullpath)
        self.dest_dirpath = get_abspath(self.mutated_path or self.src_dirpath)
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

        # Initialize the mutator
        if self.mutator:
            if not isinstance(self.mutator, dict):
                self.mutator = self.mutators.get(self.mutator, {})
        else:
            self.mutator = self.mutators.get(self.src_ext, {})

        # Make sure an appropriate mutator is defined
        if not self.mutator.get('cmd') or not self.mutator.get('ext'):
            raise RuntimeError('No mutator found for %s.' % self.src_ext)

        dest_ext = self.mutator['ext']

        # Parse the fingerprint
        if self.check_method == 'exists':
            fingerprint = hexhashify(self.src_fullpath)
        elif self.check_method == 'checksum':
            if self.batch:
                self.checksum = compute_md5(self.src_fullpath)
            else:
                self.checksum = self.checksum or compute_md5(self.src_fullpath)

            fingerprint = self.checksum
        else: # self.check_method == 'stat'
            if self.batch:
                self.stat = get_stat(self.src_fullpath)
            else:
                self.stat = self.stat or get_stat(self.src_fullpath)

            fingerprint = hexhashify(self.src_fullpath) + hexhashify(self.stat)

        # Set the destination filename/path
        self.dest_filename = '%s%s.%s.%s' % (self.prefix, self.src_name,
                                             fingerprint, dest_ext)
        self.dest_fullpath = os.path.join(self.dest_dirpath, self.dest_filename)

        # Set the new assetpath to be returned to the template
        if not self.batch:
            if self.mutated_path:
                self.new_path = self.mutated_path + self.dest_filename
            else:
                self.new_path = re.sub(r'%s$' % self.src_filename,
                                                self.dest_filename,
                                                self.path)

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
            shlex.split(cmd, posix=False),
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        data, err = proc.communicate()

        if proc.returncode != 0 or err:
            errmsg = 'Return code %s when attempting to execute %s.\n\n%s\n\n%s'
            raise EnvironmentError(errmsg % (proc.returncode,
                                             self.mutator['cmd'], err, data))

        new_dirname = os.path.normpath(os.path.dirname(self.dest_fullpath))

        if not os.path.exists(new_dirname):
            os.makedirs(new_dirname)

        with open(self.dest_fullpath, 'wb') as f:
            f.write(data)

    def mutate(self):
        """
        Mutate the asset(s) and return the new asset specification path.
        """
        if self.batch:
            for asset in glob.glob(get_abspath(self.path)):
                self.path = asset
                self._configure_paths()
                self._run_mutator()
        else:
            if self.should_mutate:
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
            raise RuntimeError('Source not found. Has it been mutated?')

        with open(self.dest_fullpath) as f:
            data = f.read()

        return data
