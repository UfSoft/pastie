from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter
from genshi.core import Markup
import operator

__all__ = ['code_highlight', 'get_lexers']

langdict = {}
for lang in get_all_lexers():
    langdict[lang[1][0]] = lang[0]

formatter = HtmlFormatter(linenos=True, cssclass="syntax", encoding='utf-8')

def code_highlight(code, truncate_lines=None):
    source = code.code
    if truncate_lines:
        split_source = source.split('\n')
        if len(split_source) > truncate_lines:
            source = split_source[:truncate_lines-1]
            source.append('...')
            source = ''.join(source)
    lexer = get_lexer_by_name(code.language, stripall=True)
    return Markup(highlight(source, lexer, formatter).decode('utf-8'))

def get_lexers():
    lexers = []
    for name, aliases, _, _ in get_all_lexers():
        if isinstance(aliases, (list, tuple)):
            aliases = aliases[0]
        lexers.append((name, aliases))
    lexers.sort(key=operator.itemgetter(0))
    return lexers
