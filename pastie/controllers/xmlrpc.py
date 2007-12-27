import logging

from pastie.lib.base import *
from pylons.controllers import XMLRPCController
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_for_filename, get_lexer_for_mimetype, guess_lexer

log = logging.getLogger(__name__)

class XmlrpcController(XMLRPCController):

    def index(self):
        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        return 'Hello World'

    def pastie_getLanguages(self):
        return h.get_lexers()
        return ["%s: %s" % (lexer[1], lexer[0]) for lexer in h.get_lexers()]

    def pastie_newPaste(self, author, title, language, code, tags=None,
                        parent_id=None, filename='', mimetype=''):

        if isinstance(tags, (tuple, list)):
            tags = ' '.join(tags)

        def get_language_for(filename, mimetype):
            try:
                lexer = get_lexer_for_mimetype(mimetype)
            except ClassNotFound:
                try:
                    lexer = get_lexer_for_filename(filename)
                except:
                    try:
                        lexer = guess_lexer(code)
                    except:
                        return 'text'
            log.debug(lexer)
            for alias in lexer.aliases:
                if alias in h.get_lexers():
                    return alias
            return 'text'
            language = get_language_for(filename or '', mimetype or '')

        paste = Paste(author, title, language, code, tags)
        Session.commit()
        return h.url_for('paste', id=paste.id, qualified=True)



