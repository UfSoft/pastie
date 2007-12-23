from pastie.tests import *

class TestPastiesController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='pasties'))
        # Test response...
