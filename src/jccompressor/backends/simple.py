from base import BaseJCBackend
import re


class SimpleJCBackend(BaseJCBackend):

    def read(self, stream):
        return self.filter_css(stream)

    def filter_css(self, text):
        pattern = u"\.top_remove_css.*\.bottom_remove_css.*?\}"
        return re.compile(pattern, re.U | re.S | re.I).sub("", text)

