# vim:fileencoding=utf-8:ai:ts=4:sts:et:sw=4:tw=80:
import os, re, glob, shlex, subprocess, hashlib
from pyramid.path import AssetResolver

class Mutator(object):
    """
    Mutator class for the pyramid_assetmutator add-on.
    """
    def __init__(self, app_settings, path, **kw):
        """
        Initialize the Mutator class.
        
        Required parameters:
        
        :type app_settings: dict
        :param app_settings: The Pyramid application ``settings`` dictionary.
        
        :type path: string
        :param path: The Pyramid ``asset path``.
        
        Optional keyword parameters:
        
        :type mutator: dict or string
        :param mutator: Allows you to either specify a specific mutator to
                         use (e.g. ``coffee``), or assign a brand new
                         mutator dictionary to be used (e.g.
                         ``{'cmd': 'lessc', 'ext': 'css'}``)
        
        :type batch: bool
        :param batch: Specify that the class should prepare for a batch
                      compile rather than a normal compile.
        """
        self.settings = app_settings
        self.path = path
        
        self.mutators = self.settings.get('assetmutator.mutators')
        self.prefix = self.settings['assetmutator.asset_prefix']
        self.check_method = self.settings['assetmutator.remutate_check']
        self.mutated_path = self.settings['assetmutator.mutated_path']
        if self.mutated_path and not self.mutated_path.endswith(os.sep):
            self.mutated_path += os.sep
        self.mutator = kw.get('mutator', None)
        
        if (not self.mutators or not isinstance(self.mutators, dict)) and \
           not self.mutator:
            raise ValueError('No mutators were found.')
        
        self.batch = kw.get('batch', False)
        self.checksum = None
        self.mtime = None
        self.exists = None
        self.mutated_dirpath = None
        
        resolver = AssetResolver()
        
        # Parse path
        self.fullpath = self.path
        if not os.path.isabs(self.path):
            # Try to resolve the asset full path
            self.fullpath = resolver.resolve(self.path).abspath()
        
        # Parse mutated_path (if specified)
        self.mutated_dirpath = self.mutated_path or None
        if self.mutated_dirpath and not os.path.isabs(self.mutated_dirpath):
            # Try to resolve the mutated_path full path
            self.mutated_dirpath = resolver.resolve(self.mutated_path).abspath()
        
        if self.batch:
            if not os.path.isdir(self.fullpath):
                raise EnvironmentError('Directory does not exist: %s' % \
                                       self.fullpath)
        
        else:
            self.filename = os.path.basename(self.fullpath)
            self.dirname = os.path.dirname(self.fullpath)
            self.name = os.path.splitext(self.filename)[0]
            self.ext = os.path.splitext(self.filename)[1][1:]
            
            if self.mutator:
                if not isinstance(self.mutator, dict):
                    self.mutator = self.mutators.get(self.mutator, {})
            else:
                self.mutator = self.mutators.get(self.ext, {})
            
            
            if not self.mutator.get('cmd') or not self.mutator.get('ext'):
                raise ValueError('No mutator found for %s' % self.ext)
    
    
    @property
    def mutated(self):
        """
        Property method to check and see if the initialized asset path has
        already been mutated.
        """
        new_ext = self.mutator['ext']
        
        if self.check_method == 'exists':
            self.new_filename = '%s%s.%s' % (self.prefix, self.name, new_ext)
        elif self.check_method == 'checksum':
            self.checksum = self.checksum or \
                            self._compute_checksum(self.fullpath)
            self.new_filename = '%s%s.%s.%s' % (self.prefix, self.name,
                                                self.checksum, new_ext)
        else: # self.check_method == 'mtime'
            self.mtime = self.mtime or self._get_mtime(self.fullpath)
            self.new_filename = '%s%s.%s.%s' % (self.prefix, self.name,
                                                self.mtime, new_ext)
        
        self.new_fullpath = os.path.join(self.mutated_dirpath or self.dirname,
                                         self.new_filename)
        
        if self.mutated_path:
            self.new_path = self.mutated_path + self.new_filename
        else:
            self.new_path = re.sub(r'%s$' % self.filename, self.new_filename,
                                            self.path)
        
        self.exists = self.exists or self._check_exists(self.new_fullpath)
        
        return self.exists
    
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
        md5.update(str(os.path.getmtime(path)))
        
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
    
    def process(self):
        """
        Runs the mutator for the initialized asset.
        """
        cmd = '%s %s' % (self.mutator['cmd'], self.fullpath)
        
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate()
        
        if proc.returncode != 0 or err:
            raise EnvironmentError('%s\n\n%s' % (err, out))
        else:
            new_dirname = os.path.normpath(os.path.dirname(self.new_fullpath))
            
            if not os.path.exists(new_dirname):
                os.makedirs(new_dirname)
            
            with open(self.new_fullpath, 'w') as f:
                f.write(out)
            
            self.exists = True
            
            return self.new_path
    
    def batch_process(self):
        """
        Runs the mutators for the initialized batch of assets.
        """
        # TODO: DRY up a bit?
        for ext, data in self.mutators.items():
            for asset in glob.glob(os.path.join(self.fullpath, '*.%s' % ext)):
                filename = os.path.basename(asset)
                dirname = os.path.dirname(asset)
                name = os.path.splitext(filename)[0]
                new_ext = data['ext']
                
                if self.check_method == 'exists':
                    new_filename = '%s%s.%s' % (self.prefix, name, new_ext)
                elif self.check_method == 'checksum':
                    checksum = self._compute_checksum(asset)
                    new_filename = '%s%s.%s.%s' % (self.prefix, name, checksum,
                                                   new_ext)
                else: # self.check_method == 'mtime'
                    mtime = self._get_mtime(asset)
                    new_filename = '%s%s.%s.%s' % (self.prefix, name, mtime,
                                                   new_ext)
                
                new_fullpath = os.path.join(self.mutated_dirpath or dirname,
                                            new_filename)
                
                if not os.path.exists(new_fullpath):
                    cmd = '%s %s' % (data['cmd'], asset)
                    
                    proc = subprocess.Popen(
                        shlex.split(cmd),
                        stdout=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    out, err = proc.communicate()
                    
                    if proc.returncode != 0 or err:
                        raise EnvironmentError('%s\n\n%s' % (err, out))
                    else:
                        new_dirname = os.path.normpath(
                            os.path.dirname(new_fullpath)
                        )
                        
                        if not os.path.exists(new_dirname):
                            os.makedirs(new_dirname)
                        
                        with open(new_fullpath, 'w') as f:
                            f.write(out)
    
    def mutated_data(self):
        if not self.exists:
            raise ValueError('Source not found. Has it been mutated?')
        
        with open(self.new_fullpath) as f:
            data = f.read()
        
        return data
