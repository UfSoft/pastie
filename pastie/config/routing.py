"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('error/:action/:id', controller='error')

    # CUSTOM ROUTES HERE
    map.connect('newpaste', '', controller='pasties', action='new')
    map.connect('xmlrpc', '/RPC2/:action/:id', controller='xmlrpc')
#    map.connect('xmlrpc', '/xmlrpc/', controller='xmlrpc', action='index')
    map.connect('list', '/list/:id', controller='pasties', action='list', id=1)
    map.connect('pastetag', '/tag/:id/:page',
                controller='pastetags', action='show', id=None, page=1)
    map.connect('tagcloud', '/tags', controller='pastetags', action='index')
    map.connect('paste', '/:id', controller="pasties", action='show')
    map.connect('pastetree', '', controller='pasties', action='tree')


    map.connect(':controller/:action/:id')
    map.connect('*url', controller='template', action='view')

    return map
