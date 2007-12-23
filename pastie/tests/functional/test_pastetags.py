from pastie.tests import *

class TestPastetagsController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='pastetags'))
        # Test response...
