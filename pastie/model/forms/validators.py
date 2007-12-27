# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: validators.py 10 2007-12-27 18:30:23Z s0undt3ch $
# =============================================================================
#             $URL: http://pastie.ufsoft.org/svn/trunk/pastie/model/forms/validators.py $
# $LastChangedDate: 2007-12-27 18:30:23 +0000 (Thu, 27 Dec 2007) $
#             $Rev: 10 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import re
import urllib2
import logging
from email.Utils import parseaddr
from urllib import urlencode
from formencode import validators, FancyValidator, Invalid
from pylons import request, config

log = logging.getLogger(__name__)

__all__ = ['AkismetValidator', 'CaptchaValidator', 'IPBlacklistValidator']

try:
    from dns.resolver import query, Timeout, NXDOMAIN, NoAnswer, NoNameservers
    HAVE_DNSPYTHON = True
except ImportError:
    HAVE_DNSPYTHON = False

class AkismetValidator(validators.UnicodeString):
    """Validator to check content against akismet"""
    api_url = 'rest.akismet.com/1.1/'
    api_key = ''
    verified_key = None

    def _to_python(self, value, state):
        try:
            return value.strip()
        except:
            return value

    def validate_python(self, value, state):
        if ('recaptcha_challenge_field' or 'recaptcha_response_field') in request.POST:
            log.debug("Skiping akismet")
            return
        print 'request', request, request.__dict__
        print
        print 'environ', request.environ
        print
        print 'config', config
        validators.UnicodeString.validate_python(self, value, state)


        base_url = "%s://%s%s%s" % (request.scheme,
                                  request.host,
                                  request.script_name,
                                  request.path_info)

        self._validade_akismet_key(base_url)

        try:
            url = 'http://%s.%scomment-check' % (self.api_key, self.api_url)
            log.debug('Checking content with Akismet service at %s', url)

            author = request.POST['author'].encode('utf-8')
            author_name, author_email = parseaddr(author)
            if not author_name and not author_email:
                author_name = author

            user_agent = request.environ['HTTP_USER_AGENT']

            params = {
                'blog': base_url,
                'user_ip': request.environ['REMOTE_ADDR'],
                'user_agent': user_agent,
                'referer': request.environ['HTTP_REFERER'] or 'unknown',
                'comment_author': author_name,
                'comment_content': value.encode('utf-8')
            }
            if author_email:
                params['comment_author_email'] = author_email

            req = urllib2.Request(url, urlencode(params),
                                  {'User-Agent' : user_agent})
            resp = urllib2.urlopen(req).read()

            log.debug('RESPONSE: %r' % resp)

            if resp.strip().lower() != 'false':
                log.debug('Akismet says content is spam')
                raise Invalid('Akismet says content is spam', value, state)

        except urllib2.URLError, e:
            log.warning('Akismet request failed (%s)', e)

    def _validade_akismet_key(self, base_url):
        log.debug("Verifying Akismet API Key")
        self.api_key = config['spamfilter.akismet_key'] or self.api_key
        self.api_url = config['spamfilter.akismet_url'] or self.api_url
        user_agent = request.environ['HTTP_USER_AGENT']

        params = {
            'blog': base_url,
            'key': self.api_key
        }

        req = urllib2.Request('http://%sverify-key' % self.api_url,
                              urlencode(params),
                              {'User-Agent': user_agent})
        resp = urllib2.urlopen(req).read()
        if resp.strip().lower() == 'valid':
            log.debug('Akismet API key is valid')
            self.verified = True
            self.verified_key = self.api_key
        return self.verified_key is not None

class IPBlacklistValidator(validators.UnicodeString):
    servers = ['bsb.empty.us', 'sc.surbl.org']

    def _to_python(self, value, state):
        log.debug('Running DNS blacklist checks')
        try:
            return value.strip()
        except:
            return value

    def validate_python(self, value, state):
        if ('recaptcha_challenge_field' or 'recaptcha_response_field') in request.POST:
            log.debug("Skiping ip blacklist")
            return
        if not HAVE_DNSPYTHON:
            log.warning("Skiping blacklist check, no dnspython package")
            return

        remote_addr = request.environ['REMOTE_ADDR']
        blacklisting_servers = []
        self.servers = config['spamfilter.blacklist.servers'].split() or \
                       self.servers

        prefix = '.'.join(reversed(remote_addr.split('.'))) + '.'
        for server in self.servers:
            try:
                query(prefix + server.encode('utf-8'))
            except NXDOMAIN: # not blacklisted on this server
                log.debug('IP: %s not blacklisted by %s', remote_addr, server)
                continue
            except (Timeout, NoAnswer, NoNameservers), e:
                log.warning('Error checking IP blacklist server "%s" for '
                            'IP "%s": %s' % (server, remote_addr, e))
            else:
                blacklisting_servers.append(server)

        if blacklisting_servers:
            raise Invalid('IP %s blacklisted by %s' % (
                            remote_addr, ', '.join(blacklisting_servers)),
                          value, state)


class CaptchaValidator(FancyValidator):

    messages = {
        'unknown': "An unknown error occurred checking captcha",
        'invalid-site-public-key': "We weren't able to verify the public key.",
        'invalid-site-private-key': "We weren't able to verify the private "
                                    "key.",
        'invalid-request-cookie': "The challenge parameter of the verify script"
                                  " is incorrect.",
        'incorrect-captcha-sol': "The CAPTCHA solution is incorrect.",
        'verify-params-incorrect': "The parameters to /verify were incorrect, "
                                   "make sure you are passing all the required "
                                   "parameters.",
        'invalid-referrer': "Invalid Referer domain. reCAPTCHA API keys are "
                            "tied to a specific domain name for security "
                            "reasons",
    }

    def _to_python(self, value, state):
        log.debug("Running captchas")
        try:
            return value.strip()
        except:
            return value

    def validate_python(self, value, state):
        if ('recaptcha_challenge_field' or 'recaptcha_response_field') not in \
            request.POST:
            log.debug('skiping captcha')
            return
        params = dict(
            privatekey = config['spamfilter.recaptcha.private_key'],
            remoteip = request.environ['REMOTE_ADDR'],
            challenge = request.POST['recaptcha_challenge_field'],
            response = request.POST['recaptcha_response_field']
        )

        user_agent = request.environ['HTTP_USER_AGENT']

        req = urllib2.Request('http://api-verify.recaptcha.net/verify',
                              urlencode(params),
                              {'User-Agent': user_agent})
        resp = urllib2.urlopen(req).read().splitlines()
        log.debug(repr(resp))
        if resp[0].strip() != 'true':

            try:
                message = self.message(resp[1].strip(), state)
            except Exception, msg:
                message = self.message('unknown', state)

            log.debug('message: %r' % message)
            raise Invalid(message, value, state)
