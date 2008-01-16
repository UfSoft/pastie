"""The base Controller API

Provides the BaseController class for subclassing, and other objects
utilized by Controllers.
"""
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, rest
from pylons.decorators.cache import beaker_cache
from pylons.decorators.secure import authenticate_form
from pylons.i18n import _, ungettext, N_
from pylons.templating import render

from pylonsgenshi.decorators import validate
from webhelpers.pagination import paginate

import pastie.lib.helpers as h
from pastie.model import Session, Paste, Tag
import pastie.model as model

class BaseController(WSGIController):

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        c.app_name = config.get('pastie_name', '')
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            Session.remove()

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
