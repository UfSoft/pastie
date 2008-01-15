"""
Author: Mike Nelson 2007
Author: Pedro Algarvio 2008

WSGI/Pylons middleware for profiling
Requires hotshot, paste, and profile packages

Usage:

Add ProfilingMiddleware ot the middleware chain in middleware.py

# YOUR MIDDLEWARE
app = ProfilingMiddleware(app,config)


There are 2 configuration directives:
#Set to True if you want to profile Every Request!
profile = True|False

#URL parameter (GET Variable) used to trigger a profile of a request
# for example:
#    www.mypylonsapp.com/mycontroller/123?__profile
# would trigger a profile of the mycontroller/123 page of your app
profile_key = __profile


"""
import hotshot, hotshot.stats
import os.path
import sys, threading, cgi
from cStringIO import StringIO

from paste import request, response
from paste.deploy.converters import asbool
from paste.wsgilib import catch_errors
from paste.httpexceptions import HTTPException
import webhelpers


__all__ = ['ProfilingMiddleware']

class ProfilingMiddleware(object):
    def __init__(self, application, app_conf,limit=40):
        self.application = application
        self.app_conf  = app_conf
        self.result = None
        self.lock = threading.Lock()
        self.limit = limit
        self.profile_get_key = self.app_conf.get("profile_key","__profile")

    def __call__(self, environ, start_response):
        profile_mode = asbool(self.app_conf.get("profile", False))
        url_params = dict(request.parse_querystring(environ))

        #AJAX call to refresh stats with different params
        if environ['PATH_INFO'].startswith("/"+self.profile_get_key):
            return self.process_ajax_request(environ,start_response)

        #generate profile inofrmation and append first page to the bottom of the page
        if profile_mode or self.profile_get_key in url_params:
            catch_response = []
            body = []
            def start_response_wrapper(status,headers, exc_info=None):
                catch_response.extend([status,headers])
                start_response(status,headers,exc_info)
                return body.append
            def run_app():
                body.extend(self.application(environ,start_response_wrapper))
            self.lock.acquire()
            try:
                here = self.app_conf['global_conf']['here']
                fname = environ['PATH_INFO'].replace('/','_')
                log_filename = os.path.join(here,fname)
                prof = hotshot.Profile(log_filename)
                url = environ.get('PATH_INFO')

                try:
                    prof.runcall(run_app)
                finally:
                    prof.close()
                body = ''.join(body)
                headers = catch_response[1]
                content_type = response.header_value(headers,'content-type')
                if not content_type.startswith('text/html'):
                    return [body]

                body += self.get_prof_shell(url_params,log_filename)
                return [body]
            finally:
                self.lock.release()

        return self.application(environ, start_response)

    def get_sort_options(self,selected=None):
        so = ['','calls','cumulative','file','module','pcalls','line','name',
              'nfl','stdname','time']
        return webhelpers.options_for_select(so,selected)

    def process_ajax_request(self,environ,start_response):
        headers = [('content-type', 'application/x-javascript')]
        start_response('200 OK',
                       headers,
                       sys.exc_info())
        print environ
        p = dict(request.parse_querystring(environ))
        print 1234, p
        limit = p.get('__limit','')
        if len(limit) == 0:
            limit = self.limit
        else:
            try:
                limit = int(limit)
            except:
                limit = self.limit

        sorts = []
        sort1 = p.get('__sort1','time')
        if len(sort1) == 0:
            sort1 = None
        else:
            sorts.append(sort1)

        sort2 = p.get('__sort2','calls')
        if len(sort2) == 0:
            sort2 = None
        else:
            sorts.append(sort2)

        show_dirs = p.get('__show_dirs',False)
        show_dirs = True if show_dirs else False

        log_filename = p.get('log_filename')

        return [self.get_prof_output(log_filename,limit,sorts,show_dirs)]

    def get_prof_shell(self,params,log_filename):
        show_dirs = params.get('__show_dirs',False)
        show_dirs = 'checked="checked"' if show_dirs else ''
        return profile_template % ({
            'stats': self.get_prof_output(log_filename),
            'action': '/__profile?', #log_filename=%s' % cgi.escape(log_filename),
            'limit' : str(self.limit),
            'log_filename': cgi.escape(log_filename),
            'sort_options1' : self.get_sort_options('time'),
            'sort_options2' : self.get_sort_options('calls'),
            'checked_show_dirs': show_dirs
        })

    def get_prof_output(self,log_filename,limit=None,sorts=['time','calls'],
                        show_dirs=False):
        out = StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        limit = limit if limit else self.limit
        try:
            stats = hotshot.stats.load(log_filename)
            if not show_dirs:
                stats.strip_dirs()
            stats.sort_stats(*sorts)
            stats.print_stats(int(limit))
            print "\n"
            stats.print_callers(int(limit))
        finally:
            sys.stdout = old_stdout
        stats_output = out.getvalue()

        return """
        <pre style="background-color: #FEFEBC;">
         %s
         </pre>
         """ % cgi.escape(stats_output)

profile_template = """
<script type="text/javascript">
  function __update_div(divObj, url) {
    alert(url);
    $(divObj).html('Loading...');
    $.ajax({
      url: url,
      success: function(data) {
          console.log(data);
          $(divObj).html(data);
          $('#__profile_div_header').scroll(); },
      error: function(req, status, error) {
          console.log(error);
          $(divObj).html(error + status); },
      type: 'GET',
    });
  }

    function __profile_form_submit(formObj) {
        var d = [
            "__limit=" + parseInt(formObj.__limit.value),
            "__sort1="  + escape(formObj.__sort1.value),
            "__sort2=" + escape(formObj.__sort2.value),
            "__show_dirs=" + formObj.__show_directories.checked,
            "log_filename=" + escape(formObj.log_filename.value)
        ]
        alert(d);
        var new_url = formObj.action + "&" + d.join("&");
        __update_div(document.getElementById('__stats_container'),new_url);
        return false;
    }
</script>
 <div style="padding: 8px; background-color: #FEFEBC; border:1px solid #EDED7A; font-weight:bold;" id="__profile_div_header">
     Profile Statistics <a href="javascript:;" onclick="var d=document.getElementById('__profile__div__');if(d.style.display=='none'){d.style.display='block'}else{d.style.display='none'}">(+)</a>
 </div>
 <div style="background-color: #FEFEBC; border:1px solid #EDED7A; display:block;" id="__profile__div__">
     <form action="%(action)s" method="get" onsubmit="return __profile_form_submit(this);">
     <table>
         <tr>
             <td>Limit</td>
             <td><input type="text" name="__limit" value="%(limit)s" size="4" /></td>
             <td>Sort Order</td>
             <td>
                 <select name="__sort1">
                     %(sort_options1)s
                 </select>
                 <select name="__sort2">
                     %(sort_options2)s
                 </select>
             </td>
             <td>
                 <input type="checkbox" name="__show_directories" %(checked_show_dirs)s/> Show Directories
             </td>
             <input type="hidden" name="log_filename" value="%(log_filename)s"/>
             <td style="padding-left: 20px;">
                 <input type="submit" value="Refresh" />
             </td>
         </tr>
     </table>
     </form>
     <div id="__stats_container">
         %(stats)s
     </div>
 </div>

"""
