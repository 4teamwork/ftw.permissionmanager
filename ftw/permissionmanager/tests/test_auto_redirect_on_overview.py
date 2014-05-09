from ftw.builder import Builder
from ftw.builder import create
from ftw.permissionmanager.testing import FTW_PERMISSIONMGR_FUNCTIONAL_TESTING
from ftw.testbrowser import browsing
from unittest2 import TestCase


class TestBuildPrincipalRoleTree(TestCase):

    layer = FTW_PERMISSIONMGR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

        self.folder = create(Builder('folder'))
        self.john = create(Builder('user').with_roles('Reader',
                                                      on=self.folder))

    @browsing
    def test_user_READER_redirect_to_principal_role_tree_view(self, browser):
        browser.login(self.john).visit(self.folder,
                                       view='@@permission_manager')

        self.assertTrue(browser.css('body.template-prinicpal_role_tree'),
                        'User with view permission should be redirected.')

    @browsing
    def test_user_ADMIN_NOT_redirected(self, browser):
        browser.login().visit(self.folder,
                              view='@@permission_manager')

        self.assertEquals(
            '{0}/@@permission_manager'.format(self.folder.absolute_url()),
            browser.url)
