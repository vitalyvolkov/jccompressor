import os

from django.conf import settings

from jccompressor import JCCompressor


try:
    from django.conf.settings import JC_MEDIA_ROOT
except:
    JC_MEDIA_ROOT=os.path.join(settings.MEDIA_ROOT,'build')


def compress_css(styles, with_ext=False):
    compress = CompressMedia(with_ext)
    return compress.get_compiled_css_url(styles)


def compress_js(scripts, with_ext=False):
    compress = CompressMedia(with_ext)
    return compress.get_compiled_js_url(scripts)


class CompressMedia:

    _with_ext = False

    def __init__(self, with_ext):
        self._with_ext = with_ext

    def get_media_url(self, url, mediatype, prefix=settings.MEDIA_URL):
        return prefix.rstrip('/') + '/%s/' % (mediatype, ) + url

    def make_compiled(self, mediatype, items):
        media_urls = []
        for item in items:
            filename = item
            if not self._with_ext:
                filename = '%s.%s' % (item, mediatype)
            url = self.get_media_url(filename, mediatype, prefix=settings.MEDIA_ROOT)
            media_urls.append(url)

        fullpath = JC_MEDIA_ROOT
        if not os.path.exists(fullpath):
            os.makedirs(fullpath)

        compressor = JCCompressor.init(fullpath, mediatype, media_urls, [])
        compressor.set_combined(
            combined = getattr(settings, 'JC_ONLY_COMBINING', False))
        compressor.process(
            version = str(getattr(settings, 'JC_SCRIPTS_VERSION', '')),
            forcebuild = getattr(settings, 'JC_FORCE_BUILD', False))
        return settings.COMPRESSED_MEDIA_URL + compressor.output_filename

    def get_compiled_js_url(self, label):
        t = '<script type="text/javascript" src="%s"></script>\n'
        if getattr(settings, 'JC_MAKE_COMPRESS', False):
            output = self.make_compiled('js', label)
            return t % output
        markup = ''
        for item in label:
            url = self.get_media_url(item, 'js')
            if not self._with_ext:
                url += '.js'
            markup += t % url
        return markup

    def get_compiled_css_url(self, label):
        t = '<link type="text/css" rel="stylesheet" href="%s" />\n'
        if getattr(settings, 'JC_MAKE_COMPRESS', False):
            output = self.make_compiled('css', label)
            return t % output
        markup = ''
        for item in label:
            url = self.get_media_url(item, 'css')
            if not self._with_ext:
                url += '.css'
            markup += t % url
        return markup
