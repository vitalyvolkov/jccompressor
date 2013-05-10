VERSION='0.1'

from jccompressor.compilers import YuiJCCompiler

import logging
logger = logging.getLogger('jccompressor')


class NoCompilerException(BaseException):
    pass


class JCCompressor(object):
    """
    Generates compressed js or css files into 1 or more compressed files

    For using package place compilers into your system PATH, so that
    JCCompressor can find it.
    """
    CSS = 'css'
    JS = 'js'

    GOOGLE_COMPILER = 'google'
    YUI_COMPILER = 'yui'

    @staticmethod
    def init(compressedest, scriptype, files=[], split_with_size=0):
        """
        Lookup available compilers and return instance of compiler
        """
        return YuiJCCompiler(scripts=files, dest=compressedest,
                             scriptype=scriptype)
