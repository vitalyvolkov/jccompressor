"""
Provides django custom tags to compress scripts inside of your applications
templates.

Collecting tags:

{% jcinclude 'my/script.js' %}
{% jcinclude 'my/another/script.css' %}

Also you can exclude one or more scripts from compressing, just use ``nocompress``
in ``jcinclude`` tag.

Example: {% jcinclude 'my/another/script.css' nocompress %}

All scripts should be placed in relative path of your MEDIA_ROOT settings.

Compressing tags:

These tags insert into your templates <link /> and <script></script> HTML tags
with link to compressed file based on your MEDIA_URL settings.

{% jccompress 'path/to/dest/build/dir' css %}
{% jccompress 'path/to/dest/build/dir' js %}


"""
import os

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from jccompressor import JCCompressor


register = template.Library()


INTERNAL_AVAILABLE_SCRIPT_TYPES = {'.js': JCCompressor.JS, '.css': JCCompressor.CSS}


class JCScript(template.Node):
    
    def __init__(self, script, attrs):
        self.script_path = template.Variable(script)
        self.attrs = attrs

    def get_scriptype(self, path):
        name, ext = os.path.splitext(path)
        avail_script = getattr(settings, 'AVAILABLE_SCRIPT_TYPES', 
                               INTERNAL_AVAILABLE_SCRIPT_TYPES)
        if ext not in avail_script.keys():
            raise template.TemplateSyntaxError, 'Extension of file ``%s`` is unavailable. Should be either `.js` or `.css`' % (os.path.basename(path),)
        return avail_script[ext]

    def prepare_attributes(self, context):
        attributes = []
        for attr in self.attrs:
            attributes.append(attr.resolve(context))
        return ' '.join(attributes)

    def render__css(self, path, context):
        attrs = self.prepare_attributes(context)
        return mark_safe('<link rel="stylesheet" href="%s" type="text/css" %s/>' % (os.path.join(settings.MEDIA_URL, path), attrs))

    def render__js(self, path, context):
        attrs = self.prepare_attributes(context)
        return mark_safe('<script src="%s" type="text/javascript" %s></script>' % (os.path.join(settings.MEDIA_URL, path), attrs))
    

class JCScriptNode(JCScript):
    nocompress = False
    compress = False
    fextract = False
    uextract = False

    def __init__(self, path, attrs = [], nocompress = False, compress = False, fextract = False, uextract = False):
        super(JCScriptNode, self).__init__(path, attrs)
        self.compress, self.nocompress, self.fextract, self.uextract = compress, nocompress, fextract, uextract
    
    def render(self, context):
        path = self.script_path.resolve(context)
        scriptype = self.get_scriptype(path)
        
        if not getattr(settings, 'JC_MAKE_COMPRESS', False) or self.nocompress:
            return getattr(self, 'render__%s' % (scriptype,))(path, context)

        files = context.get('jccompressor__%s' % (scriptype,), [])
        files.append(os.path.join(settings.MEDIA_ROOT, path))
        context['jccompressor__%s' % (scriptype,)] = files
        
        return ''


class JCScriptCompressNode(JCScript):

    def __init__(self, destpath, scriptype, attrs):
        super(JCScriptCompressNode, self).__init__(destpath, attrs)
        self.scriptype = scriptype
    
    def render(self, context):
        if not getattr(settings, 'JC_MAKE_COMPRESS', False):
            return ''

        path = self.script_path.resolve(context)

        fullpath = os.path.join(settings.MEDIA_ROOT, path)
        if not os.path.exists(fullpath):
            os.makedirs(fullpath)

        compressor = JCCompressor.init(fullpath, self.scriptype, context.get('jccompressor__%s' % (self.scriptype,), []))
        compressor.set_combined(getattr(settings, 'JC_ONLY_COMBINING', False))
        compressor.process(version = str(getattr(settings, 'JC_SCRIPTS_VERSION', '')))
        
        return getattr(self, 'render__%s' % (self.scriptype,))('build/' + compressor.output_filename, context)


@register.tag
def jcinclude(parser, token):
    bits = token.split_contents()
    tagname = bits.pop(0)
    
    if len(bits) < 1:
        raise template.TemplateSyntaxError('``%s`` must take at least one argument' % (tagname,))

    path = bits.pop(0)
    if len(bits) > 0 and bits[0] == 'nocompress':
        # set attrs without nocompress flag
        return JCScriptNode(path, attrs = [parser.compile_filter(bit) for bit in bits[1:]], nocompress = True)

    return JCScriptNode(path, attrs = [parser.compile_filter(bit) for bit in bits])


@register.tag
def jccompress(parser, token):
    '''
    {% jccompress <where> <type> <htmlattrs> %}
    '''
    bits = token.split_contents()
    tagname = bits.pop(0)
    
    if len(bits) < 2:
        raise template.TemplateSyntaxError('``%s`` must take at least one argument' % (tagname,))

    return JCScriptCompressNode(bits[0], bits[1], [parser.compile_filter(bit) for bit in bits[2:]])
