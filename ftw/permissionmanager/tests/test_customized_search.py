from ftw.permissionmanager.testing import FTW_PERMISSIONMGR_FUNCTIONAL_TESTING
import unittest as unittest
from ftw.testbrowser import browsing
from ftw.builder import create
from ftw.builder import Builder
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
import transaction


class TestRemovePermissions(unittest.TestCase):

    layer = FTW_PERMISSIONMGR_FUNCTIONAL_TESTING

    def setUp(self):
        self.user = create(Builder('user').named("John", "Smith"))
        self.folder = create(Builder('folder'))

    @browsing
    def test_fullname(self, browser):
        browser.login().visit(self.folder, view="sharing")
        browser.fill({"search_term": "Smith J"}).submit()
        self.assertEquals("Smith John",
                          browser.css("#user-group-sharing-settings a").text[0])

    @browsing
    def test_mail(self, browser):
        browser.login().visit(self.folder, view="sharing")
        browser.fill({"search_term": "john@smith"}).submit()
        self.assertEquals("Smith John",
                          browser.css("#user-group-sharing-settings a").text[0])

    @browsing
    def test_fullname_removed(self, browser):
        registry = getUtility(IRegistry)
        fields = (u'email',)
        registry["ftw.permissionmanager.fields_to_search"] = fields
        transaction.commit()
        browser.login().visit(self.folder, view="sharing")
        browser.fill({"search_term": "Smith J"}).submit()
        self.assertEquals(0,
                          len(browser.css("#user-group-sharing-settings a").text))

        browser.fill({"search_term": "john@smith"}).submit()
        self.assertEquals("Smith John",
                          browser.css("#user-group-sharing-settings a").text[0])
