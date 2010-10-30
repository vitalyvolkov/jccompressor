VERSION='0.1'

import os
from jccompressor.compilers import *

import logging
logger = logging.getLogger('jccompressor')


class NoCompilerException(BaseException):
    pass


class JCCompressor(object):
    """
    Generates compressed js or css files into 1 or more compressed files

    JCCompressor looks up available compressor scripts. For now it is 
    yui-compressor.jar and Google Closure Compiler. Priority for JS files
    is Google Compiler but you can redefine priority to yui-compresor.

    Note that Google Closure Compiler does not support CSS files, so 
    by default for them YUI is used.
    
    For using package place compilers into your system PATH, so that
    JCCompressor can find it.
    """
    CSS = 'css'
    JS = 'js'

    GOOGLE_COMPILER = 'google'
    YUI_COMPILER = 'yui'

    @staticmethod
    def init(compressedest, scriptype, files = [], prior = 'google', split_with_size = 0):
        """
        Lookup available compilers and return instance of compiler
        """
        if prior == JCCompressor.GOOGLE_COMPILER and scriptype == JCCompressor.JS:
            return GoogleJCCompiler(scripts = files, scriptype = JCCompressor.JS, dest = compressedest, split_with_size = split_with_size)
        if scriptype in [JCCompressor.JS, JCCompressor.CSS]:
            return YuiJCCompiler(scripts = files, dest = compressedest, scriptype = scriptype, split_with_size = split_with_size)
        raise NoCompilerException
