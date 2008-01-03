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
import StringIO
import re


log = logging.getLogger(__name__)

__javascript_include_tag = javascript_include_tag

__stylesheet_link_tag = stylesheet_link_tag


def javascript_include_tag(*sources, **options):

    @beaker_cache(key='sources', expire='never', type='dbm')
    def combine_sources(sources, fs_root):
        if len(sources) < 2:
            log.debug('No need to combine, only one source provided')
            return sources

        log.debug('combining javascripts: %r', sources)
        httpbase = os.path.commonprefix(['/'.join(s.split('/')[:-1])+'/'
                                         for s in sources])
        jsbuffer = StringIO.StringIO()
        names = []
        bases = os.path.commonprefix([b.split('/')[:-1] for b in sources])
        log.debug('Base: %s', httpbase)
        for source in sources:
            log.debug('appending %s', source)
            _source = os.path.join(fs_root, *(source).split('/'))
            names.append(source.split('/')[-1:][0][:-3])
            jsbuffer.write(open(_source, 'r').read())
            jsbuffer.write('\n')
        fname = '.'.join(names+['COMBINED', 'js'])
        log.debug('Names: %r', names)
        log.debug('Combined Name: %s', fname)
        fpath = os.path.join(fs_root, *((httpbase+fname).split('/')))
        log.debug('writing %s', fpath)
        open(fpath, 'w').write(jsbuffer.getvalue())
        return [httpbase + fname]

    @beaker_cache(key='sources', expire='never', type='dbm')
    def get_sources(sources, fs_root=''):
        log.debug('Generating minified sources if needed')
        from pastie.lib.jsmin import JavascriptMinify
        jsm = JavascriptMinify()
        _sources = []

        for source in sources:
            _source = os.path.join(fs_root, *(source[:-3]+'.min.js').split('/'))
            if os.path.exists(_source):
                _sources.append(source[:-3]+'.min.js')
            else:
                _source = os.path.join(fs_root, *source.split('/'))
                minified = _source[:-3]+'.min.js'
                log.debug('minifying %s -> %s', source,
                            source[:-3]+'.min.js')
                jsm.minify(open(_source, 'r'), open(minified, 'w'))
                _sources.append(source[:-3]+'.min.js')
        return _sources

    if not config.get('debug', False):
        fs_root = root = config.get('pylons.paths').get('static_files')
        if options.pop('combined', False):
            sources = combine_sources([source for source in sources], fs_root)

        if options.pop('minified', False):
            sources = get_sources([source for source in sources], fs_root)
    return __javascript_include_tag(*sources, **options)

def stylesheet_link_tag(*sources, **options):

    @beaker_cache(key='sources', expire='never', type='dbm')
    def combine_sources(sources, fs_root):
        if len(sources) < 2:
            log.debug('No need to combine, only one source provided')
            return sources

        log.debug('combining javascripts: %r', sources)
        httpbase = os.path.commonprefix(['/'.join(s.split('/')[:-1])+'/'
                                         for s in sources])
        jsbuffer = StringIO.StringIO()
        names = []
        log.debug('Base: %s', httpbase)
        for source in sources:
            log.debug('appending %s', source)
            _source = os.path.join(fs_root, *(source).split('/'))
            names.append(source.split('/')[-1:][0][:-4])
            jsbuffer.write(open(_source, 'r').read())
            jsbuffer.write('\n')
        fname = '.'.join(names+['COMBINED', 'css'])
        log.debug('Names: %r', names)
        log.debug('Combined Name: %s', fname)
        fpath = os.path.join(fs_root, *((httpbase+fname).split('/')))
        log.debug('writing %s', fpath)
        open(fpath, 'w').write(jsbuffer.getvalue())
        return [httpbase + fname]

    @beaker_cache(key='sources', expire='never', type='dbm')
    def get_sources(sources, fs_root):
        log.debug('Generating minified sources if needed')
        from pastie.lib.cssmin import CSSMinify
        cssm = CSSMinify()
        _sources = []

        for source in sources:
            _source = os.path.join(fs_root, *(source[:-4]+'.min.css').split('/'))
            if os.path.exists(_source):
                _sources.append(source[:-4]+'.min.css')
            else:
                _source = os.path.join(fs_root, *source.split('/'))
                minified = _source[:-4]+'.min.css'
                log.debug('minifying %s -> %s', source,
                            source[:-4]+'.min.css')
                cssm.minify(open(_source, 'r'), open(minified, 'w'))
                _sources.append(source[:-4]+'.min.css')
        return _sources

    if not config.get('debug', False):
        fs_root = root = config.get('pylons.paths').get('static_files')
        if options.pop('combined', False):
            sources = combine_sources([source for source in sources], fs_root)

        if options.pop('minified', False):
            sources = get_sources([source for source in sources], fs_root)
    return __stylesheet_link_tag(*sources, **options)
