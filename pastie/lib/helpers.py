"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from pylonsgenshi.helpers import *
from pastie.lib.highlight import *
from pylons import config
import os
import logging
from pylons.decorators.cache import beaker_cache


log = logging.getLogger(__name__)

__javascript_include_tag = javascript_include_tag


def javascript_include_tag(*sources, **options):
    @beaker_cache(key='sources', expire='never', type='dbm')
    def get_sources(sources):
        log.debug('Generating minified sources if needed')
        from pastie.lib.jsmin import JavascriptMinify
        jsm = JavascriptMinify()
        _sources = []
        root = config.get('pylons.paths').get('static_files')
        for source in sources:
            _source = os.path.join(root, *(source[:-3]+'.min.js').split('/'))
            if os.path.exists(_source):
                _sources.append(source[:-3]+'.min.js')
            else:
                _source = os.path.join(root, *source.split('/'))
                minified = _source[:-3]+'.min.js'
                log.debug('minifying %s -> %s', source,
                            source[:-3]+'.min.js')
                jsm.minify(open(_source, 'r'), open(minified, 'w'))
                _sources.append(source[:-3]+'.min.js')
        return _sources

    if options.pop('minified', False):
        if not config.get('debug', False):
            sources = get_sources([source for source in sources])
    return __javascript_include_tag(*sources, **options)


