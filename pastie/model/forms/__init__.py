from formencode import schema
from formencode.validators import *
from formencode.compound import All
from pastie.model.forms.validators import *

from pygments.lexers import get_all_lexers

languagelist = [lang[1][0] for lang in get_all_lexers()]

class myschema(schema.Schema):
    allow_extra_fields = True
    filter_extra_fields = True

class NewPaste(myschema):
    author = UnicodeString(max=50, not_empty=True)
    title = UnicodeString(max=60, not_empty=True)
    notabot = OneOf([u'most_likely'], hideList=True, not_empty=True)
    language = OneOf(languagelist, hideList=True, not_empty=True)
    code = All(AkismetValidator(not_empty=True),
               IPBlacklistValidator(not_empty=True))
    recaptcha_challenge_field = CaptchaValidator(if_missing=None, not_empty=True)
    tags = String()
