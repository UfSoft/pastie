import re
import cssutils
from cssutils.serialize import CSSSerializer

import logging

log = logging.getLogger(__name__)

css_comments = re.compile(r'/\*.*?\*/', re.MULTILINE|re.DOTALL)

def _css_slimmer(css):
    css = css_comments.sub('', css)
    css = re.sub(r'\s\s+', '', css)
    css = re.sub(r'\s+{','{', css)
    css = re.sub(r'\s}','}', css)
    css = re.sub(r'}','}\n', css)
    css = re.sub(r'\n\n','\n', css)
    css = re.sub(r':\s([\w\d])+', r':\1', css)
    css = re.sub(r'\n',' ', css)
    return css

class MinificationSerializer(CSSSerializer):
    def __init__(self, prefs=None):
        CSSSerializer.__init__(self, prefs)
#        cssutils.ser.useMinified(self)

#    def do_CSSStyleSheet(self, stylesheet):
#        out = []
#        for rule in stylesheet.cssRules:
#            if isinstance(rule, )
#            rule = self.change_colors(rule)
#            cssText = rule.cssText
#            if cssText:
#                out.append(cssText)
#        text = self._serialize(self.prefs.lineSeparator.join(out))
#
#        # get encoding of sheet, defaults to UTF-8
#        try:
#            encoding = stylesheet.cssRules[0].encoding
#        except (IndexError, AttributeError):
#            encoding = 'UTF-8'
#
#        return text.encode(encoding, 'escapecss')

#    def do_CSSStyleRule(self, rule):
#        CSSSerializer.do_CSSStyleRule(self, rule)

    def do_css_CSSStyleDeclaration(self, style, separator=None):
        log.debug('Style: %r, %r', style, style.seq)
        try:
            log.debug('Color: %r', style.getPropertyValue('color'))
            color = style.getPropertyValue('color')
            if color and color is not u'':
                color = self.change_colors(color)
                log.debug('Returned Color: %r', color)
                style.setProperty('color', color)
        except:
            pass
        return re.sub(r'0\.([\d])+', r'.\1',
                      re.sub(r'(([^\d][0])+(px|em)+)+', r'\2',
                      CSSSerializer.do_css_CSSStyleDeclaration(self, style,
                                                               separator)))

    def replace_zero_dot_something(self, value):
        pass

    def change_colors(self, color):
        log.debug("changing color for color: %r", color)
        colours = {
            'black': '#000000',
            'fuchia': '#ff00ff',
            'yellow': '#ffff00',
            '#808080': 'gray',
            '#008000': 'green',
            '#800000': 'maroon',
            '#000800': 'navy',
            '#808000': 'olive',
            '#800080': 'purple',
            '#ff0000': 'red',
            '#c0c0c0': 'silver',
            '#008080': 'teal'
        }
        if color.lower() in colours:
            color = colours[color.lower()]

        if color.startswith('#') and len(color) == 7:
            log.debug('Trying to reduce color length')
            if color[1]==color[2] and color[3]==color[4] and color[5]==color[6]:
                log.debug('Reduced from %s to #%s%s%s', color, color[1], color[3], color[5])
                color = '#%s%s%s' % (color[1], color[3], color[5])
        return color

class CSSMinify(object):

    def kill_comments(self):
        css_comments = re.compile(r'/\*(.*?)\*/', re.MULTILINE|re.DOTALL)
        self.instream = css_comments.sub('', self.instream)

    def kill_whitespace(self):
        self.instream = re.sub(r'\s\s+', '', self.instream)
        self.instream = re.sub(r'\s*\n*{\s*','{', self.instream)
        self.instream = re.sub(r'\s}','}', self.instream)
        self.instream = re.sub(r'}','}\n', self.instream)
        self.instream = re.sub(r'\n\n','\n', self.instream)
        self.instream = re.sub(r',\s*\n*',',', self.instream)
        self.instream = re.sub(r':\s*([^;]+);\s*', r':\1;', self.instream)

    def replace_unusefull(self):
        self.instream = re.sub(r'(([^\d][0])+(px|em)+)+', r'\2', self.instream)

    def long_colours_to_short_hex(self):
        colours = {
            '#000000': 'black',
            '#ff00ff': 'fuchsia',
            '#ffff00': 'yellow'
        }
        for key,val in colours.iteritems():
            self.instream = self.instream.replace(val, key)

    def long_hex_to_short_colours(self):
        colours = {
            '#808080': 'gray',
            '#008000': 'green',
            '#800000': 'maroon',
            '#000800': 'navy',
            '#808000': 'olive',
            '#800080': 'purple',
            '#ff0000': 'red',
            '#c0c0c0': 'silver',
            '#008080': 'teal'
        }
        for key, val in colours.iteritems():
            regex = re.compile(key, re.IGNORECASE)
            self.instream = regex.sub(val, self.instream)
            #self.instream = self.instream.replace(key, val)

    def kill_newlines(self):
#        regex = re.compile(r'\s*{([\w\d:;])\s*}', re.MULTILINE)
#        self.instream = regex.sub('{\1}\n', self.instream)
        self.instream = re.sub(r'}(\s*\n*)+',r'} ', self.instream)

    def remove_last(self):
        #self.instream = re.sub(r'([^; ]+)([\s]*)}', r'\1;', self.instream)
        self.instream = re.sub(r'(\s*(;)+\s*)}', r'}', self.instream)

    def remove_zero_dot_something(self):
        self.instream = re.sub(r'0\.([\d])+', r'.\1', self.instream)



    def minify(self, instream, outstream):
        self.instream = instream.read()
        self.sheet = cssutils.parseString(self.instream)
        serializer = MinificationSerializer()
        self.sheet.setSerializer(serializer)
        cssutils.ser.prefs.useMinified()
#        cssutils.ser.prefs.keepComments = False
#        cssutils.ser.prefs.lineSeparator=u''
#        cssutils.ser.prefs.indent=u''
#        cssutils.ser.prefs.paranthesisSpacer=u''
#        cssutils.ser.prefs.removeInvalid=False # True
#        cssutils.ser.prefs.propertyNameSpacer=u''
#        cssutils.ser.prefs.omitLastSemicolon=True
#        cssutils.ser.prefs.listItemSpacer=u''

        self.outstream = outstream
        self._cssmin()

    def _cssmin(self):
        self.replace_unusefull()
        self.remove_last()
        self.kill_comments()
        self.kill_whitespace()
#        self.long_colours_to_short_hex()
        self.long_hex_to_short_colours()
#        self.kill_newlines()
        self.remove_zero_dot_something()
#        self.outstream.write(self.instream)
        self.outstream.write(self.sheet.cssText)
