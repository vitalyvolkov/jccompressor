"""
This module defines a class :py:class:`Compiler` that combines
all of your stylesheets or javascripts files into one file with
compressing its content through yui-compiler or google-compiler.
"""

import codecs, hashlib, os, shutil

import logging
import subprocess

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from lockfile import LockFile, LockTimeout, NotLocked


logger = logging.getLogger('jccompressor.compilers')
backend = 'jccompressor.backends.simple.SimpleJCBackend'


__all__ = ('GoogleJCCompiler', 'YuiJCCompiler', 'ScriptNotFound')


class ScriptNotFound(BaseException):
    pass


class Compiler(object):

    COMPILER_PATH = os.path.join(os.path.dirname(__file__), 'build')

    def get_backend(self, filetype):
        path = getattr(settings, 'JC_BACKEND', None) or backend
        try:
            mod_name, klass_name = path.rsplit('.', 1)
            mod = import_module(mod_name)
        except ImportError, e:
            raise ImproperlyConfigured(('Error importing jccompressor backend '
                                        'module %s: "%s"' % (mod_name, e)))
        try:
            klass = getattr(mod, klass_name)
        except AttributeError:
            raise ImproperlyConfigured(('Module "%s" does not define a "%s" '
                                        ' class' % (mod_name, klass_name)))
        return klass(filetype)

    def __init__(self, scripts, scriptype, dest,
                 prefix='built', iocharset='utf-8'):
        """
        :param scripts: list of files
        :param scriptype: type of files, should be 'css' or 'js'
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
        self.backend = self.get_backend(scriptype)
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
            filename = os.path.join(settings.STATIC_ROOT, filename)
            return codecs.open(filename, mode, self.charset)
        except OSError:
            raise ScriptNotFound(filename + ' could not be opened for read or write.')

    def prepare_scripts(self, forcebuild=False):
        """ Combine all scripts into one stream.
            .. deprecated:: 1.2
            Use :func:`combine_filecontents` instead.
        """
        return self.combine_filecontents(forcebuild)

    def combine_filecontents(self, forcebuild=False):
        """
        ..py:method:: combine_filecontents([forcebuild : boolean]) -> boolean

        Combines all content of scripts into one file. Returns True if
        file generated and False if file already exists.

        :param boolean forcebuild: should re-build scripts everytime
        :rtype boolean:
        """
        _built_fname = os.path.join(self.dest, self.get_output_filename())
        if self.exists_andnot_force(forcebuild, _built_fname):
            return False

        lock_ = LockFile(os.path.join(settings.STATIC_ROOT, _built_fname))
        while lock_.i_am_locking():
            try:
                lock_.acquire(timeout=20)
            except LockTimeout:
                lock_.break_lock()
                lock_.acquire()

        try:
            _built_fd = self._openfile(_built_fname, 'w')
            # collect all content of scripts into files to be compressed
            for script in self.scripts:
                fd = self._openfile(self.backend.pre_open(script))
                content = self.backend.read(fd)
                _built_fd.write(content + '\n')
                fd.close()
            _built_fd.close()
        except:
            try:
                lock_.release()
            except NotLocked:
                pass
            return False

        return lock_

    def exists_andnot_force(self, forcebuild, _built_fname):
        return os.path.exists(_built_fname) and not forcebuild

    def process(self, version='', forcebuild=False):
        """
        Run through scripts and make compiled scripts if attribute
        ``_just_combined`` is False.
        """
        if version:
            if hasattr(version, '__call__'):
                self.prefix += '.v%s.' % version(self.scriptype)
            else:
                self.prefix += '.v%s.' % (str(version),)
        lock_ = self.combine_filecontents(forcebuild)
        if not lock_:
            # File already exists, so no need to regenerate it again
            return False
        if self._just_combined:
            try:
                lock_.release()
            except NotLocked:
                pass
            return True
        filename = os.path.join(self.dest, self.output_filename)
        try:
            self.compile(filename)
            return True
        except (OSError, IOError, subprocess.CalledProcessError), e:
            logger.error('%r: %s', type(e), e)
        try:
            lock_.release()
        except NotLocked:
            pass
        return False

    def compile(self):
        """ This method is called to start compress file. It is intended
        to be overridden by a derived class; the base class implementation
        does nothing.
        """
        return None

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
            '-jar',
            '%s/compiler.jar' % Compiler.COMPILER_PATH,
            '--js',
            filename,
            '--js_output_file',
            '%s.tmp' % filename,
            '--charset',
            self.charset]
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
            '-Xss1M',
            '-jar',
            '%s/yuicompressor.jar' % Compiler.COMPILER_PATH,
            '-o',
            '%s.tmp' % filename,
            '--type',
            self.scriptype,
            '--charset',
            self.charset,
            filename]

        # using compiler place compressed content into temporary file
        # and then we replace original combined file with this one
        subprocess.check_call(attrs)
        shutil.move(filename + '.tmp', filename)
        return True
