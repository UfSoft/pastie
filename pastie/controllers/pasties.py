import re
import logging

from pastie.lib.base import *
from pastie.lib.highlight import formatter, langdict
from sqlalchemy import desc, func
#from alternativepaginator import Page
from pastie.lib.paginator import Page

log = logging.getLogger(__name__)

class PastiesController(BaseController):

    def __before__(self):
        c.model = model
        c.langdict = langdict

    @rest.dispatch_on(POST="new_POST")
    def new(self, id=None):
        log.debug('On new')
        c.tags = [str(tag.name) for tag in Session.query(Tag).all()]
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
        cache.get_cache('pasties.list').clear()
        cache.get_cache('pastetags.show').clear()
        redirect_to('paste', id=paste.id)

    def index(self, id=1):
        redirect_to(action='list', id=id)

    @beaker_cache(key=None, expire=45, type="memory") #, query_args=True)
    def list(self, id):
        c.paginator = Page(Session.query(Paste), current_page=id or 1,
                           items_per_page=25,
                           sqlalchemy_engine=config['pylons.g'].sa_engine)
        log.debug(c.paginator)
        return render('paste.index')

    def show(self, id):
        if not re.match(r'^\d+$', id):
            abort(404)

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
        print c.paste, c.id
        return render('paste.tree')
