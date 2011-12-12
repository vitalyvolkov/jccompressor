from distutils.core import setup
import os


data_dir = 'src/jccompressor/build'
data_files = []


for dirpath, dirnames, filenames in os.walk(data_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    for fname in filenames:
        data_files.append(os.path.join(dirpath, fname).replace('src/jccompressor/', ''))


setup(name="jccompressor",
      version="0.2a",
      description="Simple compressor for js and css files",
      author="Vitaly Volkov",
      author_email="vw@vedjo.com.ua",
      packages=['jccompressor', 'jccompressor.ext', 'jccompressor.ext.django',
                'jccompressor.ext.django.templatetags', 'jccompressor.ext.jinja2',
                'jccompressor.backends'],
      package_dir={'jccompressor':'src/jccompressor'},
      package_data={'jccompressor': data_files},
      url="http://hash.naikonsoft.com/jccompressor/")
