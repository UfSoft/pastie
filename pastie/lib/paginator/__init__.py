"""
Pagination module for lists and ORMs

This module helps dividing large lists of items into pages. The user gets
displayed one page at a time and can navigate to other pages. Imagine you are
offering a company phonebook and let the user search the entries. If the search
result contains 23 entries but you may want to display  no more than 10 entries
at one. The first page contains entries 1-10, the second 11-20 and the third
21-23. See the documentation of the "Page" class for more information. This
module is especially useful for Pylons web framework applications.

Compatibility warning:

This pagination module is an alternative to the paginator that comes with the
webhelpers module. It is in no way compatible so just replacing the import
statements will break your code. It just uses the webhelpers.pagination.orm
module though.

This software can be used under the terms of the MIT license:

Copyright (c) 2007 Christoph Haas <email@christoph-haas.de>
Copyright (c) 2007 James Gardner <james@3aims.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Parts of this module are based on the webhelpers.pagination.orm module written
by Ben Bangert <ben@groovie.org> and Phil Jenvey <pjenvey@groovie.org> which
is available under the BSD license from http://pylonshq.com/WebHelpers/
"""

# Import the webhelpers to create URLs
import webhelpers

# For nose unit tests
from routes import Mapper

import re

# Deprecation warnings
import warnings

__version__ = '0.2.0beta'
__author__ = 'Christoph Haas <email@christoph-haas.de>, James Gardner <james@3aims.com>'

# import SQLAlchemy if available
try:
    import sqlalchemy
except:
    sqlalchemy_available = False
else:
    sqlalchemy_available = sqlalchemy.__version__

def get_wrapper(obj, sqlalchemy_engine=None):
    """
    Auto-detect the kind of object and return a list/tuple
    to access items from the collection.
    """
    # See if the collection is a sequence
    if isinstance(obj, (list, tuple)):
        return obj
    # Is SQLAlchemy 0.4 available? (0.3 is not supported - sorry)
    if sqlalchemy_available.startswith('0.4'):
        # Is the collection a query?
        if isinstance(obj, sqlalchemy.orm.query.Query):
            return _SQLAlchemyQuery(obj)

        # Is the collection an SQLAlchemy table?
        # (A table can't be used directly because it's just a definition of a
        # schema. It doesn't give us enough information to query data from it.
        # We still need a databae connection.)
        if isinstance(obj, sqlalchemy.schema.Table):
            # If a Table object is passed then we also need an engine so we
            # can run SELECT queries on the database.
            if isinstance(sqlalchemy_engine, sqlalchemy.engine.base.Engine):
                return _SQLAlchemyTable(obj, sqlalchemy_engine)
            else:
                raise TypeError("If you want to page an SQLAlchemy 'Table' object then you "
                        "have to provide an 'sqlalchemy_engine' argument. See also: "
                        "http://www.sqlalchemy.org/docs/04/sqlexpression.html#sql_selecting")

    raise TypeError("Sorry, your collection type is not supported by the paginator. "
            "You can either provide a list, a tuple, an SQLAlchemy table or an "
            "SQLAlchemy query object.")

class _SQLAlchemyTable(object):
    """
    Iterable that allows to get slices from an SQLAlchemy Table object
    """
    def __init__(self, obj, sqlalchemy_engine):
        self.sqlalchemy_engine = sqlalchemy_engine
        self.obj = obj

    def __getitem__(self, range):
        if not isinstance(range, slice):
            raise Exception, "__getitem__ without slicing not supported"
        offset = range.start
        limit = range.stop - range.start
        select = sqlalchemy.select([self.obj]).offset(offset).limit(limit)
        return self.sqlalchemy_engine.execute(select).fetchall()

    def __len__(self):
        select = sqlalchemy.select([self.obj])
        return self.sqlalchemy_engine.execute(select).rowcount

class _SQLAlchemyQuery(object):
    """
    Iterable that allows to get slices form an SQLAlchemy Query object
    """
    def __init__(self, obj):
        self.obj = obj

    def __getitem__(self, range):
        if not isinstance(range, slice):
            raise Exception, "__getitem__ without slicing not supported"
        return self.obj[range]

    def __len__(self):
        return self.obj.count()


# Since the items on a page are mainly a list we subclass the "list" type
class Page(list):
    """
    A list/iterator of items representing one page in a larger collection

    An instance of the "Page" class is created from a collection of things.
    The instance works as an iterator running from the first item to the last
    item on the given page. The collection can be:

    - a sequence
    - an SQLObject instance
    - an SQLAlchemy query
    - an SQLAlchemy table

    A "Page" instance maintains pagination logic associated with each page,
    where it begins, what the first/last item on the page is, etc. The
    navigator() method creates a link list allowing the user to go to
    other pages.

    **WARNING:** Unless you pass in an item_count, a count will be performed
    on the collection every time a Page instance is created. If using an ORM,
    it's advised to pass in the number of items in the collection if that
    number is known.

    Instance attributes:

    original_collection
        Points to the collection object being paged through

    item_count
        Number of items in the collection

    current_page
        Number of the current page

    first_page
        Number of the first page - starts with 1

    last_page
        Number of the last page

    page_count
        Number of pages

    items
        Sequence/iterator of items on the current page

    item_count
        Number of items in the collection

    first_item
        Index of first item on the current page

    last_item
        Index of last item on the current page
    """
    def __init__(self, collection, current_page=1, items_per_page=20,
        item_count=None, sqlalchemy_engine=None, *args, **kwargs):
        """
        Create a "Page" instance.

        Parameters:

        collection
            Sequence, SQLObject, SQLAlchemy table or SQLAlchemy query
            representing the collection of items to page through.

        current_page
            The requested page number - starts with 1. Default: 1.

        items_per_page
            The maximal number of items to be displayed per page.
            Default: 20.

        item_count (optional)
            The total number of items in the collection - if known.
            If this parameter is not given then the paginator will count
            the number of elements in the collection every time a "Page"
            is created. Giving this parameter will speed up things.

        sqlalchemy_engine (optional)
            If you want to use an SQLAlchemy (0.4) table as a collection
            then you need to provide an 'engine' object here. A 'Table'
            object does not have a database connection attached so the paginator
            wouldn't be able to execute a SELECT query without it.
        """
        # 'page_nr' is deprecated. 'current_page' is clearer and used by Ruby-on-Rails, too
        if 'page_nr' in kwargs:
            warnings.warn("'page_nr' is deprecated. Please use current_page instead.")
            current_page = kwargs['page_nr']

        # Save a reference to the collection
        self.original_collection = collection

        # Decorate the ORM/sequence object with __getitem__ and __len__
        # functions to be able to get slices.
        if collection:
            # Determine the type of collection and use a wrapper for ORMs
            self.collection = get_wrapper(collection, sqlalchemy_engine)
        else:
            self.collection = []

        # The self.current_page is the number of the current page.
        # The first page has the number 1!
        try:
            self.current_page = int(current_page) # make it int() if we get it as a string
        except ValueError:
            self.current_page = 1

        self.items_per_page = items_per_page

        # Unless the user tells us how many items the collections has
        # we calculate that ourselves.
        if item_count:
            self.item_count = item_count
        else:
            self.item_count = len(self.collection)

        # Compute the number of the first and last available page
        if self.item_count > 0:
            self.first_page = 1
            self.page_count = ((self.item_count - 1) / self.items_per_page) + 1
            self.last_page = self.first_page + self.page_count - 1

            # Make sure that the requested page number is the range of valid pages
            if self.current_page > self.last_page:
                self.current_page = self.last_page
            elif self.current_page < self.first_page:
                self.current_page = self.first_page

            # Note: the number of items on this page can be less than
            #       items_per_page if the last page is not full
            self.first_item = (self.current_page - 1) * items_per_page
            self.last_item = min(self.first_item + items_per_page - 1, self.item_count - 1)

            # We subclassed "list" so we need to call its init() method
            # and fill the new list with the items to be displayed on the page
            self.items = self.collection[self.first_item:self.last_item+1]

        # No items available
        else:
            self.first_page = None
            self.page_count = 0
            self.last_page = None
            self.first_item = None
            self.last_item = None
            self.items = []

        # This is a subclass of the 'list' type. Initialise the list now.
        list.__init__(self, self.items)


    def __repr__(self):
        return ("Paginator:\n"
            "Collection type:  %(type)s\n"
            "Current page:     %(current_page)s\n"
            "First item:       %(first_item)s\n"
            "Last item:        %(last_item)s\n"
            "First page:       %(first_page)s\n"
            "Last page:        %(last_page)s\n"
            "Items per page:   %(items_per_page)s\n"
            "Number of items:  %(item_count)s\n"
            "Number of pages:  %(page_count)s\n"
            % {
            'type':type(self.collection),
            'current_page':self.current_page,
            'first_item':self.first_item,
            'last_item':self.last_item,
            'first_page':self.first_page,
            'last_page':self.last_page,
            'items_per_page':self.items_per_page,
            'item_count':self.item_count,
            'page_count':self.page_count,
            })

    def pager(self, format='~2~', link_var='page_nr',
        show_if_single_page=False, separator=' ',
        ajax_id=None, framework='scriptaculous',
        symbol_first='&lt;&lt;', symbol_last='&gt;&gt;',
        symbol_previous='&lt;', symbol_next='&gt;',
        link_attr={'class':'pager_link'}, curpage_attr={'class':'pager_curpage'},
        dotdot_attr={'class':'pager_dotdot'}, **kwargs):
        """
        Return a string containing links to other pages (e.g. "1 2 [3] 4 5 6 7 8")

        format:
            Format string that defines how the pager is rendered. The string
            can contain the following %-tokens:

            - %(first_page)s: number of first reachable page
            - %(last_page)s: number of last reachable page
            - %(current_page)s: number of currently selected page
            - %(page_count)s: number of reachable pages
            - %(items_per_page)s: maximal number of items per page
            - %(first_item)s: index of first item on the current page
            - %(last_item)s: index of last item on the current page
            - %(item_count)s: total number of items
            - %(link_first)s: link to first page (unless this is the first page)
            - %(link_last)s: link to last page (unless this is the last page)
            - %(link_previous)s: link to previous page (unless this is the first page)
            - %(link_next)s: link to next page (unless this is the last page)

            To render a range of pages the token '~3~' can be used. The number
            sets the radius of pages around the current page.
            Example for a range with radius 3: '1 .. 5 6 7 [8] 9 10 11 .. 500'

            Default: '~2~'

        symbol_first
            String to be displayed as the text for the %(link_first)s link above.

            Default: '&lt;&lt;' ('<<')

        symbol_last
            String to be displayed as the text for the %(link_last)s link above.

            Default: '&gt;&gt;' ('>>')

        symbol_previous
            String to be displayed as the text for the %(link_previous)s link above.

            Default: '&lt;' ('<

        symbol_next
            String to be displayed as the text for the %(link_next)s link above.

            Default: '&gt;' ('>')

        separator:
            String that is used to seperate page links/numbers in the above range
            of pages.

            Default: ' '

        link_var:
            The name of the parameter that will carry the number of the page the
            user just clicked on. The parameter will be passed to a url_for()
            call so if you stay with the default ':controller/:action/:id'
            routing and set link_var='id' then the :id part of the URL will be
            changed. If you set link_var='current_page' then url_for() will make it
            an extra parameters like ':controller/:action/:id?current_page=1'. You
            need the link_var in your action to determine the page number the
            user wants to see. If you do not specify anything else the default
            will be a parameter called 'current_page'.

        show_if_single_page:
            if True the navigator will be shown even if there is only one page
            (default: False)

        link_attr (optional)
            A dictionary of attributes that get added to A-HREF links pointing
            to other pages. Can be used to define a CSS style or class to
            customize the look of links.

            Example: { 'style':'border: 1px solid green' }

            Default: { 'class':'pager_link' }

        curpage_attr (optional)
            A dictionary of attributes that get added to the current page
            number in the pager (which is obviously not a link).
            If this dictionary is not empty then the elements
            will be wrapped in a SPAN tag with the given attributes.

            Example: { 'style':'border: 3px solid blue' }

            Default: { 'class':'pager_curpage' }

        dotdot_attr (optional)
            A dictionary of attributes that get added to the '..' string
            in the pager (which is obviously not a link).
            If this dictionary is not empty then the elements
            will be wrapped in a SPAN tag with the given attributes.

            Example: { 'style':'color: #808080' }

            Default: { 'class':'pager_dotdot' }

        framework
            The name of the JavaScript framework to use. By default
            the AJAX functions from script.aculo.us are used. Supported
            frameworks:
            - scriptaculous
            - jquery

        ajax_id (optional)
            If this parameter is given then the navigator will add Javascript to
            the A-HREF links that will update only a portion of the web page
            instead of reloading the copmlete page.

            This parameter contains the name of the HTML element (e.g. a <div
            id="foobar">) that the paginator should replace with the new
            content.
            The navigator will create AJAX links (e.g. using webhelpers'
            link_to_remote() function) that replace the HTML element's content
            with the new page of paginated items and a new navigator.

        framework
            The name of the Javascript framework to use. By default
            the AJAX functions from script.aculo.us are used. Supported
            Javascript frameworks:

            - scriptaculous (Default)
            - jquery
            - yui2.3 (Yahoo UI library)

        Additional keyword arguments are used as arguments in the links.
        Otherwise the link will be created with url_for() which points to
        the page you are currently displaying.
        """

        def _pagerlink(pagenr, text):
            """
            Create a URL that links to another page using url_for()

            Parameters:
                
            pagenr
                Number of the page that the link points to

            text
                Text to be printed in the A-HREF tag
            """
            # Let the url_for() from webhelpers create a new link and set
            # the variable called 'link_var'. Example:
            # You are in '/foo/bar' (controller='foo', action='bar')
            # and you want to add a parameter 'pagenr'. Then you
            # call the navigator method with link_var='pagenr' and
            # the url_for() call will create a link '/foo/bar?pagenr=...'
            # with the respective page number added.
            link_params = {}
            link_params[link_var] = pagenr
            link_url = webhelpers.url_for(**link_params)
            if ajax_id:
                # Return an AJAX link that will update the HTML element
                # named by ajax_id.
                if framework == 'scriptaculous':
                    return webhelpers.link_to_remote(text, dict(update=ajax_id, url=link_url),
                        **link_attr)
                elif framework == 'jquery':
                    return webhelpers.link_to(text,
                        onclick="""$('#%s').load('%s'); return false""" % (ajax_id, link_url),
                            **link_attr)
                elif framework == 'yui2.3':
                    js = """
                        var callback = {
                            success: function(o) {
                                YAHOO.util.Dom.get('%s').innerHTML = o.responseText;
                             },
                            failure: function(o) {
                                alert('Failed to update the paginator.\\nPlease try again.');
                            }
                        }; 
                        sUrl = '%s';
                        var transaction = YAHOO.util.Connect.asyncRequest('GET', sUrl, callback, null);
                        return false;
                    """ % (ajax_id, link_url)
                    return webhelpers.link_to(text, onclick=js, **link_attr)
                else:
                    raise Exception, "Unsupported Javascript framework: %s" % framework

            else:
                # Return a normal a-href link that will call the same
                # controller/action with the link_var set to the new
                # page number.
                return webhelpers.link_to(text, link_url, **link_attr)

        #------- end of def _pagerlink

        def _range(regexp_match):
            """
            Return range of linked pages (e.g. '1 2 [3] 4 5 6 7 8')

            Arguments:
                
            regexp_match
                A "re" (regular expressions) match object containing the
                radius of linked pages around the current page in
                regexp_match.group(1) as a string

            This funtion is supposed to be called as a callable in re.sub
            """
            radius = int(regexp_match.group(1))

            # Compute the first and last page number within the radius
            # e.g. '1 .. 5 6 [7] 8 9 .. 12'
            # -> leftmost_page  = 5
            # -> rightmost_page = 9
            leftmost_page = max(self.first_page, (self.current_page-radius))
            rightmost_page = min(self.last_page, (self.current_page+radius))

            nav_items = []

            # Create a link to the first page (unless we are on the first page
            # or there would be no need to insert '..' spacers)
            if self.current_page != self.first_page and self.first_page<leftmost_page:
                nav_items.append( _pagerlink(self.first_page, self.first_page) )

            # Insert dots if there are pages between the first page
            # and the currently displayed page range
            if leftmost_page - self.first_page > 1:
                # Wrap in a SPAN tag if nolink_attr is set
                text = '..'
                if dotdot_attr:
                    text = webhelpers.tag('span', open=True, **dotdot_attr) + text + '</span>'
                nav_items.append(text)

            for thispage in xrange(leftmost_page, rightmost_page+1):
                # Hilight the current page number and do not use a link
                if thispage == self.current_page:
                    text = '%s' % (thispage,)
                    # Wrap in a SPAN tag if nolink_attr is set
                    if curpage_attr:
                        text = webhelpers.tag('span', open=True, **curpage_attr) + text + '</span>'
                    nav_items.append(text)
                # Otherwise create just a link to that page
                else:
                    text = '%s' % (thispage,)
                    nav_items.append( _pagerlink(thispage, text) )

            # Insert dots if there are pages between the displayed
            # page numbers and the end of the page range
            if self.last_page - rightmost_page > 1:
                text = '..'
                # Wrap in a SPAN tag if nolink_attr is set
                if dotdot_attr:
                    text = webhelpers.tag('span', open=True, **dotdot_attr) + text + '</span>'
                nav_items.append(text)

            # Create a link to the very last page (unless we are on the last
            # page or there would be no need to insert '..' spacers)
            if self.current_page != self.last_page and rightmost_page<self.last_page:
                nav_items.append( _pagerlink(self.last_page, self.last_page) )

            return separator.join(nav_items)

        #------- end of def _range


        # Don't show navigator if there is no more than one page
        if self.page_count == 0 or (self.page_count == 1 and not show_if_single_page):
            return ''


        # Replace ~...~ in token format by range of pages
        result = re.sub(r'~(\d+)~', _range, format)

        # Interpolate '%' variables
        result = result % {
            'first_page': self.first_page,
            'last_page': self.last_page,
            'current_page': self.current_page,
            'page_count': self.page_count,
            'items_per_page': self.items_per_page,
            'first_item': self.first_item,
            'last_item': self.last_item,
            'item_count': self.item_count,
            'link_first': self.current_page>self.first_page and \
                    _pagerlink(self.first_page, symbol_first) or '',
            'link_last': self.current_page<self.last_page and \
                    _pagerlink(self.last_page, symbol_last) or '',
            'link_previous': self.current_page>self.first_page and \
                    _pagerlink(self.current_page-1, symbol_previous) or '',
            'link_next': self.current_page<self.last_page and \
                    _pagerlink(self.current_page+1, symbol_next) or ''
        }

        return result


    # navigator - still available but deprecated
    def navigator(self, link_var='page_nr', radius=2,
        start_with_one=True, seperator=' ', show_if_single_page=False,
        ajax_id=None, framework='scriptaculous', **kwargs):
        """
        Returns a list of links to other page before and after the current
        page. Example: "1 2 [3] 4 5 6 7 8". 

        link_var:
            The name of the parameter that will carry the number of the page the
            user just clicked on. The parameter will be passed to a url_for()
            call so if you stay with the default ':controller/:action/:id'
            routing and set link_var='id' then the :id part of the URL will be
            changed. If you set link_var='page_nr' then url_for() will make it
            an extra parameters like ':controller/:action/:id?page_nr=1'. You
            need the link_var in your action to determine the page number the
            user wants to see. If you do not specify anything else the default
            will be a parameter called 'page_nr'.

        radius:
            The number of pages left and right to the current page shown in the
            navigator. Examples::

                mypaginator.navigator(radius=1)    # the default
                1 .. 7 [8] 9 .. 500

                mypaginator.navigator(radius=3)
                1 .. 5 6 7 [8] 9 10 11 .. 500

                mypaginator.navigator(radius=5)
                1 .. 3 4 5 6 7 [8] 9 10 11 12 13 .. 500

        start_with_one:
            page numbers start with 0. If this flag is True then the user will
            see page numbers start with 1.

        seperator:
            the string used to seperate the page links (default: ' ')

        show_if_single_page:
            if True the navigator will be shown even if there is only one page
            (default: False)

        Additional keyword arguments are used as arguments in the links.
        Otherwise the link will be created with url_for() which points to
        the page you are currently displaying.
        """

        def _link(pagenr, text):
            """
            Create a URL that links to another page
            """
            # Let the url_for() from webhelpers create a new link and set
            # the variable called 'link_var'. Example:
            # You are in '/foo/bar' (controller='foo', action='bar')
            # and you want to add a parameter 'pagenr'. Then you
            # call the navigator method with link_var='pagenr' and
            # the url_for() call will create a link '/foo/bar?pagenr=...'
            # with the respective page number added.
            # Further kwargs that are passed to the navigator will
            # also be added as URL parameters.
            arg_dict = {link_var:pagenr}
            arg_dict.update(kwargs)
            link_url = webhelpers.url_for(**arg_dict)
            if ajax_id:
                # Return an AJAX link that will update the HTML element
                # named by ajax_id.
                if framework == 'scriptaculous':
                    return webhelpers.link_to_remote(text, dict(update=ajax_id,
                        url=link_url))
                elif framework == 'jquery':
                    return webhelpers.link_to(text,
                        onclick="""$('#%s').load('%s'); return false""" % \
                        (ajax_id, link_url))
                else:
                    raise exception, "Unsupported Javascript framework: %s" % \
                            framework

            else:
                # Return a normal a-href link that will call the same
                # controller/action with the link_var set to the new
                # page number.
                return webhelpers.link_to(text, link_url)


        warnings.warn('The navigator() method is deprecated. Please use pager().')

        # Don't show navigator if there is no more than one page
        if self.page_count <= 1 and show_if_single_page == False:
            return ''

        # Compute the number of pages before/after the current page
        leftmost_page = max(self.first_page, (self.current_page-radius))
        rightmost_page = min(self.last_page, (self.current_page+radius))

        nav_items = []

        # Create a link to the very first page (unless we are there already)
        if self.current_page != self.first_page and leftmost_page>self.first_page:
            text = '%s' % (self.first_page+(start_with_one and 1)-1)
            nav_items.append(_link(self.first_page+1, text))

        # Insert dots if there are pages between the first page
        # and the currently displayed page range
        if self.first_page < leftmost_page-1:
            nav_items.append('..')

        for thispage in xrange(leftmost_page, rightmost_page+1):
            # Hilight the current page number without a link
            if thispage == self.current_page:
                text = '[<strong>%s</strong>]' % (thispage+(start_with_one and 1)-1)
                nav_items.append(text)
            # Otherwise create just a link to that page
            else:
                text = '%s' % (thispage+(start_with_one and 1)-1)
                nav_items.append(_link(thispage+(start_with_one and 1)-1, text))

        # Insert dots if there are pages between the displayed
        # page numbers and the end of the page range
        if self.last_page > rightmost_page+1:
            nav_items.append('..')

        # Create a link to the very last page (unless we are there already)
        if self.current_page != self.last_page and rightmost_page<self.last_page:
            text = '%s' % (self.last_page+(start_with_one and 1)-1)
            nav_items.append(_link(self.last_page+(start_with_one and 1)-1, text))
        return seperator.join(nav_items)

# Unit tests (useing Nose 0.9.3)
def testEmptyList():
    """
    Test: Tests whether an empty list is handled correctly.
    """
    items = []
    # Create routes mapper so that webhelper can create URLs
    # using webhelpers.url_for()
    map = Mapper()
    map.connect(':controller')
    paginator = Page(items, current_page=0)
    assert paginator.current_page==0
    assert paginator.first_item is None
    assert paginator.last_item is None
    assert paginator.first_page is None
    assert paginator.last_page is None
    assert paginator.items_per_page==20
    assert paginator.item_count==0
    assert paginator.page_count==0
    # Test deprecated navigator()
    assert paginator.navigator()==''
    assert paginator.pager()==''
    assert paginator.pager(show_if_single_page=True)==''

def testOnePage():
    """
    Test: Tries to fit 10 items on a 10-item page
    """
    items = range(10)
    # Create routes mapper so that webhelper can create URLs
    # using webhelpers.url_for()
    map = Mapper()
    map.connect(':controller')
    paginator = Page(items, current_page=0, items_per_page=10)
    assert paginator.current_page==1
    assert paginator.first_item==0
    assert paginator.last_item==9
    assert paginator.first_page==1
    assert paginator.last_page==1
    assert paginator.items_per_page==10
    assert paginator.item_count==10
    assert paginator.page_count==1
    # Test deprecated navigator()
    assert paginator.navigator()==''
    assert paginator.pager()==''
    assert paginator.pager(show_if_single_page=True)=='<span class="pager_curpage">1</span>'

def testManyPages():
    """
    Test: Tries to fit 100 items on 15-item pages
    """
    items = range(100)
    # Create routes mapper so that webhelper can create URLs
    # using webhelpers.url_for()
    map = Mapper()
    map.connect(':controller')
    paginator = Page(items, current_page=0, items_per_page=15)
    assert paginator.current_page==1
    assert paginator.first_item==0
    assert paginator.last_item==14
    assert paginator.first_page==1
    assert paginator.last_page==7
    assert paginator.items_per_page==15
    assert paginator.item_count==100
    assert paginator.page_count==7
    # Test deprecated navigator()
    assert paginator.navigator()=='[<strong>1</strong>] <a href="/content?page_nr=2">2</a> <a href="/content?page_nr=3">3</a> .. <a href="/content?page_nr=7">7</a>'
    assert paginator.pager()=='<span class="pager_curpage">1</span> <a href="/content?page_nr=2" class="pager_link">2</a> <a href="/content?page_nr=3" class="pager_link">3</a> <span class="pager_curpage">..</span> <a href="/content?page_nr=7" class="pager_link">7</a>'
    assert paginator.pager(separator='_')=='<span class="pager_curpage">1</span>_<a href="/content?page_nr=2" class="pager_link">2</a>_<a href="/content?page_nr=3" class="pager_link">3</a>_<span class="pager_curpage">..</span>_<a href="/content?page_nr=7" class="pager_link">7</a>'
    assert paginator.pager(link_var='xy')=='<span class="pager_curpage">1</span> <a href="/content?xy=2" class="pager_link">2</a> <a href="/content?xy=3" class="pager_link">3</a> <span class="pager_curpage">..</span> <a href="/content?xy=7" class="pager_link">7</a>'
    assert paginator.pager(link_attr={'style':'s1'},curpage_attr={'style':'s2'},dotdot_attr={'style':'s3'})=='<span style="s2">1</span> <a href="/content?page_nr=2" style="s1">2</a> <a href="/content?page_nr=3" style="s1">3</a> <span style="s3">..</span> <a href="/content?page_nr=7" style="s1">7</a>'

if __name__ == '__main__':
    map = Mapper()
    map.connect(':controller')

# vim:tw=100:

