from zope.component import getMultiAdapter
from ftw.permissionmanager.testing import (
    FTW_PERMISSIONMGR_FUNCTIONAL_TESTING,
    TEST_USER_ID_2, TEST_GROUP_ID, TEST_GROUP_ID_2)
import unittest2 as unittest
from plone.app.testing import TEST_USER_NAME, TEST_USER_PASSWORD, TEST_USER_ID
from plone.testing.z2 import Browser
import transaction


class TestCopyPermissions(unittest.TestCase):

    layer = FTW_PERMISSIONMGR_FUNCTIONAL_TESTING

    def setUp(self):
        self.browser = Browser(self.layer['app'])
        self.browser.handleErrors = False

    def test_copy_permission_view(self):
        portal = self.layer['portal']
        view = getMultiAdapter(
            (portal.folder1, portal.folder1.REQUEST),
            name="copy_user_permissions")
        self.assertTrue(view.__name__ == 'copy_user_permissions')

    def test_copy_permission_form_user(self):
        portal = self.layer['portal']
        portal_url = portal.absolute_url()

        # Set local roles for test user
        portal.portal_membership.setLocalRoles(
            obj=portal.folder1,
            member_ids=[TEST_USER_ID],
            member_role="Contributor",
            reindex=True)
        portal.folder1.reindexObjectSecurity()

        portal.portal_membership.setLocalRoles(
            obj=portal.folder1.folder2,
            member_ids=[TEST_USER_ID],
            member_role="Editor",
            reindex=True)
        portal.folder1.folder2.reindexObjectSecurity()

        transaction.commit()  # for test self.browser

        # Login as test user
        self.browser.open(portal_url + '/login_form')
        self.browser.getControl(name='__ac_name').value = TEST_USER_NAME
        self.browser.getControl(
            name='__ac_password').value = TEST_USER_PASSWORD
        self.browser.getControl(name='submit').click()

        self.browser.open(portal_url + '/folder1/copy_user_permissions')

        # Look for the right form
        self.assertIn(
            '<form method="post" action="http://nohost/plone/folder1/'
            '@@copy_user_permissions">',
            self.browser.contents)

        # Search for the test user
        self.browser.getControl(name="search_source_user").value = TEST_USER_ID
        self.browser.getControl(name="submit").click()
        self.assertIn(
            '<a href="http://nohost/plone/folder1/@@copy_user_permissions?'
            'source_user=test_user_1_">test_user_1_</a>',
            self.browser.contents)

        # Choose user
        self.browser.open('http://nohost/plone/folder1/@@copy_user_'
                          'permissions?source_user=test_user_1_')
        self.assertIn(
            '<input type="hidden" name="source_user" value="test_user_1_" />',
            self.browser.contents
        )

        # Choose target user
        self.browser.getControl(
            name="search_target_user").value = TEST_USER_ID_2
        self.browser.getControl(name="submit").click()
        self.assertIn(
            '<a href="http://nohost/plone/folder1/@@copy_user_permissions?'
            'target_user=_test_user_2_&amp;source_user=test_user_1_">'
            '_test_user_2_</a>',
            self.browser.contents
        )

        self.browser.open('http://nohost/plone/folder1/@@copy_user_'
                          'permissions?target_user=_test_user_2_&amp;'
                          'source_user=test_user_1_')

        # Confirm link
        self.assertIn(
            '<a class="context" href="http://nohost/plone/folder1/@@copy_'
            'user_permissions?source_user=test_user_1_&amp;target_user='
            '_test_user_2_&amp;confirm=1">',
            self.browser.contents)

        # Abort link
        self.assertIn(
            '<a class="standalone" href="http://nohost/plone/folder1/'
            '@@copy_user_permissions">',
            self.browser.contents)

        self.browser.open('http://nohost/plone/folder1/@@copy_user_'
                          'permissions?source_user=test_user_1_&amp;target_'
                          'user=_test_user_2_&amp;confirm=1')

        # After permission copy, redirect to copy permission view again
        self.assertIn(
            'class="template-copy_user_permissions',
            self.browser.contents)

        # Approve if test user 2 has the same local roles
        self.assertTrue(
            portal.folder1.get_local_roles_for_userid(TEST_USER_ID_2) ==
                ('Owner', 'Contributor'))
        self.assertFalse(
            portal.folder1.get_local_roles_for_userid(TEST_USER_ID_2) ==
                ('Owner', 'Editor'))

    def test_copy_permission_form_group(self):
        portal = self.layer['portal']
        portal_url = portal.absolute_url()

        # Set up two groups
        portal.portal_groups.addGroup(TEST_GROUP_ID)
        portal.portal_groups.addGroup(TEST_GROUP_ID_2)
        # Add local roles
        portal.folder1.manage_addLocalRoles(TEST_GROUP_ID, ['Contributor', ])
        portal.folder1.reindexObjectSecurity()
        portal.folder1.folder2.manage_addLocalRoles(TEST_GROUP_ID,
                                                    ['Editor', ])
        portal.folder1.folder2.reindexObjectSecurity()

        transaction.commit()  # for test self.browser

        # Login as test user
        self.browser.open(portal_url + '/login_form')
        self.browser.getControl(name='__ac_name').value = TEST_USER_NAME
        self.browser.getControl(
            name='__ac_password').value = TEST_USER_PASSWORD
        self.browser.getControl(name='submit').click()

        self.browser.open(portal_url + '/folder1/copy_user_permissions')

        # Look for the right form
        self.assertIn(
            '<form method="post" action="http://nohost/plone/folder1/'
            '@@copy_user_permissions">',
            self.browser.contents)

        # Search for the test group
        self.browser.getControl(
            name="search_source_user").value = TEST_GROUP_ID
        self.browser.getControl(name="submit").click()
        self.assertIn(
            '<a href="http://nohost/plone/folder1/@@copy_user_permissions?'
            'source_user=test_group">test_group</a>',
            self.browser.contents)

        # Choose group
        self.browser.open('http://nohost/plone/folder1/@@copy_user_'
                          'permissions?source_user=test_group')
        self.assertIn(
            '<input type="hidden" name="source_user" value="test_group" />',
            self.browser.contents
        )

        # Choose target user
        self.browser.getControl(
            name="search_target_user").value = TEST_GROUP_ID_2
        self.browser.getControl(name="submit").click()
        self.assertIn(
            '<a href="http://nohost/plone/folder1/@@copy_user_permissions?'
            'target_user=test_group_2&amp;source_user=test_group">'
            'test_group_2</a>',
            self.browser.contents
        )

        self.browser.open('http://nohost/plone/folder1/@@copy_user_'
                          'permissions?target_user=test_group_2'
                          '&amp;source_user=test_group')

        # Confirm link
        self.assertIn(
            '<a class="context" href="http://nohost/plone/folder1/@@copy_'
            'user_permissions?source_user=test_group&amp;target_user='
            'test_group_2&amp;confirm=1">',
            self.browser.contents)

        # Abort link
        self.assertIn(
            '<a class="standalone" href="http://nohost/plone/folder1/'
            '@@copy_user_permissions">',
            self.browser.contents)

        self.browser.open('http://nohost/plone/folder1/@@copy_user_'
            'permissions?source_user=test_group&amp;target_user='
            'test_group_2&amp;confirm=1')

        # After permission copy, redirect to copy permission view again
        self.assertIn(
            'class="template-copy_user_permissions',
            self.browser.contents)

        for id_, roles in dict(portal.folder1.get_local_roles()).items():
            if id_ == TEST_GROUP_ID_2:
                break
        self.assertIn('Contributor', roles)
        results = dict(portal.folder1.folder2.get_local_roles()).items()
        for id_, roles in results:
            if id_ == TEST_GROUP_ID_2:
                break
        self.assertIn('Editor', roles)

