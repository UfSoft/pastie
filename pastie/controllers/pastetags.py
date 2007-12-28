import logging

from pastie.lib.base import *

log = logging.getLogger(__name__)

class PastetagsController(BaseController):

    @beaker_cache(expire=120)
    def index(self):
        c.tag_sizes = Paste.tag_sizes()
        log.debug(c.tag_sizes)
        return render('pastetags.tagcloud')

#    @beaker_cache(expire=45, type="ext:memcached", query_args=True)
    @beaker_cache(expire=45, type="memory", query_args=True)
    def show(self, id):
        query_args = [Paste.tags.any(name=str(id))]
        c.paginator, c.pastes = paginate(Paste.query(), per_page=20,
                                         query_args=query_args,
                                         _session=Session)
        return render('pastetags.show')
