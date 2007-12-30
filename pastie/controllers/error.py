import os.path

import paste.fileapp
from pylons.middleware import error_document_template, media_path

from pastie.lib.base import *

class ErrorController(BaseController):
    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.
    """

    def document(self):
        prefix=request.environ.get('SCRIPT_NAME', '')
        code = request.params.get('code', '')
        message = request.params.get('message', '')
        if not config.get('debug', False):
            return self.pastie_document(prefix, code, message)
        return self.pylons_document(prefix, code, message)

    def pastie_document(self, prefix, code, message):
        c.code = code
        c.error_message = message
        return render('error.index')

    def pylons_document(self, prefix, code, message):
        """Render the error document"""
        page = error_document_template % \
            dict(prefix=prefix, code=code, message=message)
        return page

    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file(os.path.join(media_path, 'img', id))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file(os.path.join(media_path, 'style', id))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        fapp = paste.fileapp.FileApp(path)
        return fapp(request.environ, self.start_response)
