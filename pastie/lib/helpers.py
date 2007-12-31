"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from pylonsgenshi.helpers import *
from pastie.lib.highlight import *
from pylons import config
import os
import logging

log = logging.getLogger(__name__)

from webhelpers.rails.asset_tag import compute_public_path, javascript_builtins

__javascript_include_tag = javascript_include_tag

def javascript_include_tag(*sources, **options):
    if options.pop('minified', False):
        from pastie.jsmin import JavascriptMinify
        jsm = JavascriptMinify()
        if not config.get('debug', False):
            root = config.get('pylons.paths').get('static_files')
            _sources = []
            for source in sources:
                _source = os.path.join(root, *(source[:-3]+'.min.js').split('/'))
                if os.path.exists(_source):
                    _sources.append(source[:-3]+'.min.js')
                else:
                    _source = os.path.join(root, *source.split('/'))
                    minified = _source[:-3]+'.min.js'
                    log.warning('minifying %s -> %s', source,
                                source[:-3]+'.min.js')
                    jsm.minify(open(_source, 'r'), open(minified, 'w'))
                    _sources.append(source[:-3]+'.min.js')
            sources = _sources
    return __javascript_include_tag(*sources, **options)


