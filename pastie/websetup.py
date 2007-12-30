"""Setup the Pastie application"""
import logging

from paste.deploy import appconfig
from pylons import config
from sqlalchemy import *
import os

from pastie.config.environment import load_environment

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup pastie here"""
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)

    import pastie.model as model

    if not conf.has_key('sqlalchemy.url'):
        raise KeyError("No sqlalchemy database config found!")
    print "Connecting to database %s..."%repr(conf['sqlalchemy.url'])
    engine = create_engine(conf['sqlalchemy.url'])

    model.metadata.drop_all(engine)

    print "Creating tables"
    model.metadata.create_all(engine)

    print "Minifying javascripts"
    import os
    from jsmin import JavascriptMinify
    jsbase = os.path.join(os.path.dirname(__file__), 'public', 'js')
    for js in ['jquery-latest.js', 'jquery.easing.js', 'jquery.autocomplete.js']:
        jsm = JavascriptMinify()
        jspath = os.path.join(jsbase, js)
        minified = os.path.join(jsbase, js[:-3]+'.min.js')
        print '  ', jspath, '->', minified,
        jsm.minify(open(jspath, 'r'), open(minified, 'w'))
        print 'Done'
    print "Successfully setup"

