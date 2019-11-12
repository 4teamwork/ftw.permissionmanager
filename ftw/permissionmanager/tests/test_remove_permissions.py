from ftw.builder import Builder
from ftw.builder import create
from ftw.permissionmanager.testing import FTW_PERMISSIONMGR_FUNCTIONAL_TESTING
from ftw.testbrowser import browsing
import transaction
import unittest as unittest


class TestRemovePermissions(unittest.TestCase):

    layer = FTW_PERMISSIONMGR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    @browsing
    def test_remove_permission_form_user(self, browser):
        folder1 = create(Builder('folder').titled(u'folder1'))
        folder2 = create(Builder('folder').titled(u'folder2').within(folder1))

        create(Builder('user').named('Hugo', 'Boss'))
        folder1.manage_addLocalRoles('hugo.boss', ['Editor'])
        folder2.manage_addLocalRoles('hugo.boss', ['Contributor'])
        folder1.reindexObjectSecurity()

        # Approve if user has local roles on folder1 and folder2
        self.assertIn('hugo.boss', dict(folder1.get_local_roles()))
        self.assertIn('hugo.boss', dict(folder2.get_local_roles()))

        # Search user
        browser.login().visit(self.portal, view='remove_user_permissions')
        browser.fill({'search_term': 'hugo.boss'}).submit()

        # Choose user
        browser.find('Boss Hugo').click()

        # test confirm text
        expected_text = ['Are you sure to remove all permissions of Boss Hugo (hugo.boss) '
                         'on object "Plone site" and all sub objects?']
        actual_text = browser.css('.text-confirm-remove').normalized_text()
        self.assertEquals(expected_text, actual_text)

        # Confirm removal of roles
        browser.css('button.context').first.click()

        # After removal, redirect to permission manager overview
        expected_url = 'http://nohost/plone/@@permission_manager'
        self.assertEquals(expected_url, browser.url)

        # Approve if user has no local roles on folder1 and folder2
        self.assertNotIn('hugo.boss', dict(folder1.get_local_roles()))
        self.assertNotIn('hugo.boss', dict(folder2.get_local_roles()))

    @browsing
    def test_remove_permission_form_group(self, browser):
        self.portal = self.layer['portal']

        folder1 = create(Builder('folder').titled(u'folder1'))
        folder2 = create(Builder('folder').titled(u'folder2').within(folder1))

        create(Builder('group').titled('Group Oldies'))
        folder1.manage_addLocalRoles('group-oldies', ['Editor'])
        folder2.manage_addLocalRoles('group-oldies', ['Contributor'])
        folder1.reindexObjectSecurity()

        # Search user
        browser.login().visit(self.portal, view='remove_user_permissions')
        browser.fill({'search_term': 'group-oldies'}).submit()

        # Choose user
        browser.find('Group Oldies').click()

        # test confirm text
        expected_text = ['Are you sure to remove all permissions of Group Oldies (group-oldies) '
                         'on object "Plone site" and all sub objects?']
        actual_text = browser.css('.text-confirm-remove').normalized_text()
        self.assertEquals(expected_text, actual_text)

        # Confirm removal of roles
        browser.css('button.context').first.click()

        # After removal, redirect to permission manager overview
        expected_url = 'http://nohost/plone/@@permission_manager'
        self.assertEquals(expected_url, browser.url)

        # Approve if user has no local roles on folder1 and folder2
        self.assertNotIn('group-oldies', dict(folder1.get_local_roles()))
        self.assertNotIn('group-oldies', dict(folder2.get_local_roles()))

    @browsing
    def test_abort_deletion_of_permissions(self, browser):
        folder1 = create(Builder('folder').titled(u'folder1'))
        folder2 = create(Builder('folder').titled(u'folder2').within(folder1))

        create(Builder('group').titled('Group Oldies'))
        folder1.manage_addLocalRoles('group-oldies', ['Editor'])
        folder2.manage_addLocalRoles('group-oldies', ['Contributor'])
        folder1.reindexObjectSecurity()
        transaction.commit()

        # Search user
        browser.login().visit(self.portal, view='remove_user_permissions')
        browser.fill({'search_term': 'group-oldies'}).submit()

        # Choose user
        browser.find('Group Oldies').click()

        # Abort removal of roles
        browser.find('No, abort').click()

        # After abort, redirect to permission manager overview
        expected_url = 'http://nohost/plone/@@remove_user_permissions'
        self.assertEquals(expected_url, browser.url)

        # Approve if user has no local roles on folder1 and folder2
        self.assertIn('group-oldies', dict(folder1.get_local_roles()))
        self.assertIn('group-oldies', dict(folder2.get_local_roles()))
