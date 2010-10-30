import unittest, os
from jccompressor import JCCompressor
from jccompressor.compilers import Compiler, ScriptNotFound


class TestCompressor(unittest.TestCase):

    directory = os.path.join(os.path.dirname(__file__), 'files')
    jcs = [
        directory + '/1.js', 
        directory + '/2.js', 
        directory + '/3.js']
    css = [
        directory + '/1.css', 
        directory + '/2.css', 
        directory + '/3.css']
    
    def test_get_compiler(self):
        compressor = JCCompressor.init(self.directory, scriptype = JCCompressor.JS)
        self.assert_(Compiler in type(compressor).__mro__, 'No compiler instances defined')

    def test_get_output_single_filename(self):
        compressor = self.get_jsc_compressor()
        self.assertEquals(compressor.output_filename, 'compilb3d1f67.js')

    def test_get_output_combined_single_file(self):
        compressor = self.get_jsc_compressor()
        self.assertTrue(compressor.prepare_scripts())
        self.assertFalse(compressor.prepare_scripts())
        self.remove_compiled(compressor)

    def test_get_output_compressed_single_file(self):
        compressor = self.get_jsc_compressor()
        compressor.process()
        self.remove_compiled(compressor)
        
    def test_get_stylesheet_file(self):
        compressor = JCCompressor.init(self.directory, files = self.css, scriptype = JCCompressor.CSS)
        self.assertEquals(compressor.output_filename, 'compilb2f9399.css')
        self.remove_compiled(compressor, assertion = False)
        compressor.process()
        self.remove_compiled(compressor)

    def test_raise_script_not_found(self):
        compressor = JCCompressor.init(self.directory, files = ['fail.css'], scriptype = JCCompressor.CSS)
        self.remove_compiled(compressor, assertion = False)
        self.assertRaises(ScriptNotFound, compressor.process)
        

    def get_jsc_compressor(self):
        compressor = JCCompressor.init(self.directory, files = self.jcs, scriptype = JCCompressor.JS)
        self.remove_compiled(compressor, assertion = False)
        return compressor

    def remove_compiled(self, compressor, assertion = True):
        filename = os.path.join(self.directory, compressor.output_filename)
        if assertion:
            self.assert_(os.path.exists(filename))
        try:
            os.remove(filename)
        except OSError:
            pass
