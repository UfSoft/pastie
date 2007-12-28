import re
import logging

from pastie.lib.base import *
from pastie.lib.highlight import formatter, langdict
from sqlalchemy import desc, func

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
        paste = Paste(author, title, language, code, tags)
        #Session.save_or_update(paste)
        #Session.save(paste)
        Session.commit()
        redirect_to('paste', id=paste.id)

#    @beaker_cache(expire=45, type="ext:memcached", query_args=True)
    @beaker_cache(expire=45, type="memory", query_args=True)
    def index(self):
        show_today = request.GET.get('restrict', '') == 'today'
        if show_today:
            query_args = [func.date(Paste.c.date)==func.current_date()]
        else:
            query_args = []
#        c.paginator, c.pastes = paginate(Session.query(Paste).all(),
        c.paginator, c.pastes = paginate(Paste.query(),
                                         per_page=20,
                                         query_args=query_args,
                                         _session=Session)
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
