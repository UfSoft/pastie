import logging

from pastie.lib.base import *
from pastie.lib.paginator import Page

log = logging.getLogger(__name__)

class PastetagsController(BaseController):

    @beaker_cache(expire=120)
    def index(self):
        c.tag_sizes = Paste.tag_sizes()
        log.debug(c.tag_sizes)
        return render('pastetags.tagcloud')

#    @beaker_cache(expire=45, type="ext:memcached", query_args=True)
    @beaker_cache(key=None, expire=45, type="memory", query_args=True)
    def show(self, id, page=1):
        query = Session.query(Paste).filter(Paste.tags.any(name=str(id)))
        c.paginator = Page(query, current_page=page or 1, items_per_page=25,
                           sqlalchemy_engine=config['pylons.g'].sa_engine)
        return render('pastetags.show')
