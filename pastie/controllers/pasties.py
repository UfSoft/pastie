import re
import logging

from pastie.lib.base import *
from pastie.lib.highlight import formatter, langdict
from sqlalchemy import desc, func
from pastie.lib.paginator import Page

log = logging.getLogger(__name__)

class PastiesController(BaseController):

    @rest.dispatch_on(POST="new_POST")
    def new(self, id=None):
        log.debug('On new')
        c.tags = [str(tag.name) for tag in Session.query(Tag).all()]
        c.author = request.cookies.get('author', '')
        c.language = request.cookies.get('language', '')
        c.public_key = config['spamfilter.recaptcha.public_key']
        if id:
            c.parent = Session.query(Paste).get(int(id))
            log.debug("Replying to paste with id: %s", id)

        c.authentication_token = h.authentication_token()
        return render('paste.new')


    @authenticate_form
    @validate(template='paste.new', schema=model.forms.NewPaste(), form='new')
    def new_POST(self, id=None):
        log.debug('On create')
        author = request.POST.get('author')
        title = request.POST.get('title')
        language = request.POST.get('language')
        code = request.POST.get('code')
        tags = request.POST.get('tags')
        parent_id = request.POST.get('parent_id', None)
        if parent_id is u'':
           parent_id = None
        log.debug('Parent ID: %r', parent_id)
        paste = Paste(author, title, language, code, tags, parent_id=parent_id)
        Session.commit()

        # Clear the pastes listing
        log.debug('Clearing pasties list cache')
        cache.get_cache('pastie.controllers.pasties.list').clear()
        # Clear the tagcloud
        log.debug('Clear the tagcloud')
        cache.get_cache('pastie.controllers.pastetags.index').clear()
        # Clear the "pastes with tag" cache
        tagscache = cache.get_cache('pastie.controllers.pastetags.show')
        for tag in paste.tags:
            tagscache.remove_value(tag.name)

        # Set some defaults on user cookie
        response.set_cookie('language', language, expires=31556926)
        response.set_cookie('author', author, expires=31556926)
        redirect_to('paste', id=paste.id)

    def index(self, id=1):
        redirect_to(action='list', id=id)

    # One hour cache
    @beaker_cache(key='id', expire=3600, type="memory")
    def list(self, id):
        c.paginator = Page(Session.query(Paste), current_page=id or 1,
                           items_per_page=25,
                           sqlalchemy_engine=config['pylons.g'].sa_engine)
        log.debug(c.paginator)
        return render('paste.index')

    def show(self, id):
        if not re.match(r'^\d+$', id):
            abort(404)
        c.langdict = langdict
        paste = Session.query(Paste).filter_by(id=id).first()
        if not paste:
            abort(404)

        c.paste = paste
        c.styles = formatter.get_style_defs('.syntax')
        return render('paste.show')

    def tree(self, id):
        paste = Paste.resolve_root(int(id))
        if not paste:
            abort(404)
        c.paste = paste
        c.id = int(id)
        return render('paste.tree')

    def download(self, id):
        if not id:
            redirect_to('list')
        paste = Session.query(Paste).get(int(id))
        if not paste:
            abort(404)

        mimetype = h.get_lexer_by_name(paste.language or 'text').mimetypes[0]
        response.content_type__set(mimetype)
        response.charset__set('utf-8')
        response.write(paste.code)
        return

    @beaker_cache(expire='never', type='memory') # don't expire cache
    def diff(self, id=None, parent=None):
        c.langdict = langdict
        c.paste = Session.query(Paste).get(int(id))
        c.parent = Session.query(Paste).get(int(parent))
        return render('paste.diff')
