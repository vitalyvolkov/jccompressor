import codecs, hashlib, os, shutil
import datetime
import logging
import subprocess


logger = logging.getLogger('jccompressor.compilers')


__all__ = ('GoogleJCCompiler', 'YuiJCCompiler', 'ScriptNotFound')


class ScriptNotFound(BaseException):
    pass


class Compiler(object):
    """
    Base class to compile scripts.

    It contains abstract method `compile` that have to be defined in
    inheritanced classes.
    """

    COMPILER_PATH = os.path.join(os.path.dirname(__file__), 'build')

    def __init__(self, scripts, scriptype, dest, 
                 prefix='built', iocharset='utf-8', split_with_size=0):
        """
        :param scripts: list of scripts
        :param scriptype: type of scripts, should be 'css' or 'js'
        :param dest: path to save built file
        :param prefix: prefix of built file (default: 'built')
        :param iocharset: result encoding for built file (default: utf-8)
        :param split_with_size: max size of built script (not implemented yet)
        """
        self.scriptype = scriptype
        self.scripts = scripts
        self.prefix = prefix
        self.charset = iocharset
        self.dest = dest
        self.split_with_size = split_with_size
        assert isinstance(split_with_size, int)
        assert scriptype in ['css', 'js']

    def set_combined(self, combined):
        self._just_combined = combined

    def set_output_filename(self, value):
        """ Set new name for built file. """
        self._output_filename = value

    def get_output_filename(self):
        """ Returns name of file to built. """
        if self._output_filename:
            return self._output_filename
        result = ''
        for f in self.scripts:
            result += os.path.basename(f)
        
        suff = self._getunique_shakey(result)[:7]
        self._output_filename = self.prefix + suff + '.' + self.scriptype
        return self._output_filename
    output_filename = property(get_output_filename)

    def _getunique_shakey(self, value):
        """ Returns digest of sha for value. """
        newsha = hashlib.new('sha')
        newsha.update(value)
        return newsha.hexdigest()

    def _openfile(self, filename, mode='r'):
        """ Open file and returns its descriptor. 
        
        :param filename: path to file
        :param mode: mode for opening
        :raises: ScriptNotFound
        :returns: opened file descriptor
        """
        try:
            return codecs.open(filename, mode, self.charset)
        except OSError:
            raise ScriptNotFound(filename + ' could not be opened for read or write.')

    def prepare_scripts(self, forcebuild=False):
        """
        Combines all content of scripts into one file. Returns True if 
        file generated and False if file already exists.

        :param forcebuild: should re-build scripts everytime
        """
        _built_fname = os.path.join(self.dest, self.get_output_filename())
        if self.exists_andnot_force(forcebuild, _built_fname):
            return False
        _built_fd = self._openfile(_built_fname, 'w')
        # collect all content of scripts into files to be compressed
        for script in self.scripts:
            if self.split_with_size:
                # @todo implement splitting
                pass
            fd = self._openfile(script)
            _built_fd.write(fd.read())
            fd.close()
        _built_fd.close()
        return True

    def exists_andnot_force(self, forcebuild, _built_fname):
        return os.path.exists(_built_fname) and not forcebuild

    def process(self, version='', forcebuild=False):
        """ 
        Run through scripts and make compiled scripts if attribute 
        ``_just_combined`` is False.
        """
        if version:
            self.prefix += '.v%s.' % (str(version),)
        if not self.prepare_scripts(forcebuild):
            # File already exists, so no need to regenerate it again
            return False
        if self._just_combined:
            return True
        filename = os.path.join(self.dest, self.output_filename)
        try:
            return self.compile(filename)
        except OSError, e:
            logger.error('OSError: %s', e)
        return False

    def compile(self):
        raise NotImplementedError

    _output_filename = None
    _just_combined = False
    
    def get_extended_scripts(self):
        """ Not implemented """
        raise NotImplementedError
    _extended_scripts = []


class GoogleJCCompiler(Compiler):
    
    def compile(self, filename):
        """
        Executes google jc compiler command.

        :param filename: file name of compiled version of script
        """
        attrs = [
            'java',
            '-jar %s/compiler.jar' % Compiler.COMPILER_PATH,
            '--js %s' % filename,
            '--js_output_file %s.tmp' % filename,
            '--charset %s' % self.charset]
        subprocess.check_call(attrs)
        shutil.move(filename + '.tmp', filename)
        return True


class YuiJCCompiler(Compiler):
    
    def compile(self, filename):
        """
        Executes yui compiler command

        :param filename: file name of compiled version of script
        """
        attrs = [
            'java',
            '-jar %s/yuicompressor.jar' % Compiler.COMPILER_PATH,
            '-o %s.tmp' % filename,
            '--type %s' % self.scriptype,
            '--charset %s' % self.charset,
            '%s' % filename]

        # using compiler place compressed content into temporary file
        # and then we replace original combined file with this one
        subprocess.check_call(attrs)
        shutil.move(filename + '.tmp', filename)
        return True
