import re
import logging

from pastie.lib.base import *
from pastie.lib.highlight import formatter, langdict
from sqlalchemy import desc, func
#from alternativepaginator import Page
from pastie.lib.paginator import Page

log = logging.getLogger(__name__)

class PastiesController(BaseController):

    @rest.dispatch_on(POST="new_POST")
    def new(self, id=None):
        log.debug('On new')
        c.tags = [str(tag.name) for tag in Session.query(Tag).all()]
        if 'author' in request.cookies:
            c.author = request.cookies['author']
        else:
            c.author = ''
        if 'language' in request.cookies:
            c.language = request.cookies['language']
        else:
            c.language = ''
        c.public_key = config['spamfilter.recaptcha.public_key']
        if id:
            c.parent = Session.query(Paste).get(int(id))
            log.debug("Replying to paste with id: %s", id)
        return render('paste.new')

    @validate(template='paste.new', schema=model.forms.NewPaste(), form='new')
    def new_POST(self, id=None):
        log.debug('On create')
        author = request.POST['author']
        title = request.POST['title']
        language = request.POST['language']
        code = request.POST['code']
        tags = request.POST['tags']
        parent_id = request.POST['parent_id']
        paste = Paste(author, title, language, code, tags, parent_id=parent_id)
        #Session.save_or_update(paste)
        #Session.save(paste)
        Session.commit()

        # Clear the pastes listing
        cache.get_cache('pastie.controllers.pasties.list').clear()
        # Clear the tagcloud
        cache.get_cache('pastie.controllers.pastetags.index').clear()
        # Clear the "pastes with tag" chache
        tagscache = cache.get_cache('pastie.controllers.pastetags.show')
        for tag in paste.tags:
            tagscache.remove_value(tag.name)

        # Set some defaults on user cookie
        response.set_cookie('language', language, expires=31556926)
        response.set_cookie('author', author, expires=31556926)
        redirect_to('paste', id=paste.id)

    def index(self, id=1):
        redirect_to(action='list', id=id)

    # One how cache
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
