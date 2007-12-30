from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter
from genshi import XML
import operator
import StringIO

__all__ = ['code_highlight', 'get_lexers']

langdict = {}
for lang in get_all_lexers():
    langdict[lang[1][0]] = lang[0]



class PastieHtmlFormatter(HtmlFormatter):
    def __init__(self, **options):
        HtmlFormatter.__init__(self, **options)
        self.lineanchorlinks = options.get('lineanchorlinks', False)

    def _wrap_tablelinenos(self, inner):
        dummyoutfile = StringIO.StringIO()
        lncount = 0
        for t, line in inner:
            if t:
                lncount += 1
            dummyoutfile.write(line)

        fl = self.linenostart
        mw = len(str(lncount + fl - 1))
        sp = self.linenospecial
        st = self.linenostep
        s = self.lineanchors
        if sp:
            if self.lineanchorlinks:
                ls = '\n'.join([(i%st == 0 and
                                 (i%sp == 0 and '<a href="#%s-%d" class="lineanchorlinks"><span class="special">%*d</span></a>'
                                  or '<a class="lineanchorlinks" href="#%s-%d">%*d</a>') % (s, i, mw, i)
                                 or '')
                                for i in range(fl, fl + lncount)])
            else:
                ls = '\n'.join([(i%st == 0 and
                                 (i%sp == 0 and '<span class="special">%*d</span>'
                                  or '%*d') % (mw, i)
                                 or '')
                                for i in range(fl, fl + lncount)])
        else:
            if self.lineanchorlinks:
                ls = '\n'.join([(i%st == 0 and ('<a class="lineanchorlinks" href="#%s-%d">%*d</a>' % (s, i, mw, i)) or '')
                                for i in range(fl, fl + lncount)])

            else:
                ls = '\n'.join([(i%st == 0 and ('%*d' % (mw, i)) or '')
                                for i in range(fl, fl + lncount)])

        yield 0, ('<table class="%stable">' % self.cssclass +
                  '<tr><td class="linenos"><pre>' +
                  ls + '</pre></td><td class="code">')
        yield 0, dummyoutfile.getvalue()
        yield 0, '</td></tr></table>'

    def _wrap_inlinelinenos(self, inner):
        # need a list of lines since we need the width of a single number :(
        lines = list(inner)
        sp = self.linenospecial
        st = self.linenostep
        num = self.linenostart
        mw = len(str(len(lines) + num - 1))
        s = self.lineanchors

        if sp:
            if self.lineanchorlinks:
                for t, line in lines:
                    yield 1, '<a href="#%s-%d" class="lineanchorlinks"><span class="lineno%s">%*s</span></a> ' % (
                        s, num, num%sp == 0 and ' special' or '', mw, (num%st and ' ' or num)) + line
                    num += 1
            else:
                for t, line in lines:
                    yield 1, '<span class="lineno%s">%*s</span> ' % (
                        num%sp == 0 and ' special' or '', mw, (num%st and ' ' or num)) + line
                    num += 1
        else:
            if self.lineanchorlinks:
                for t, line in lines:
                    yield 1, '<a href="#%s-%d" class="lineanchorlinks"><span class="lineno">%*s</span></a> ' % (
                        s, num, mw, (num%st and ' ' or num)) + line
                    num += 1
            else:
                for t, line in lines:
                    yield 1, '<span class="lineno">%*s</span> ' % (
                        mw, (num%st and ' ' or num)) + line
                    num += 1

formatter = PastieHtmlFormatter(linenos=True, cssclass="syntax",
                                encoding='utf-8', lineanchors='line',
                                lineanchorlinks=True, linenospecial=10)

def code_highlight(code, truncate_lines=None):
    source = code.code
    if truncate_lines:
        split_source = source.split('\n')
        if len(split_source) > truncate_lines:
            source = split_source[:truncate_lines-1]
            source.append('...')
            source = ''.join(source)
    lexer = get_lexer_by_name(code.language or 'text', stripall=True)
    return XML(highlight(source, lexer, formatter).decode('utf-8'))

def get_lexers(sorted_list=False):
    lexers = {}
    for name, aliases, _, _ in get_all_lexers():
        if isinstance(aliases, (list, tuple)):
            aliases = aliases[0]
        lexers[aliases] = name
    #lexers.sort(key=operator.itemgetter(0))
    return lexers

