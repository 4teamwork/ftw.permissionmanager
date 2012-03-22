from zope.component import getMultiAdapter
from ftw.permissionmanager.testing import FTW_PERMISSIONMANAGER_INTEGRATION_TESTING
import unittest2 as unittest
from plone.app.testing import TEST_USER_NAME, TEST_USER_PASSWORD, TEST_USER_ID
from plone.testing.z2 import Browser
import transaction

class TestRemovePermissions(unittest.TestCase):

    layer = FTW_PERMISSIONMANAGER_INTEGRATION_TESTING


    def test_remove_permission_view(self):
        portal = self.layer['portal']
        view = getMultiAdapter(
            (portal.folder1, portal.folder1.REQUEST),
            name="remove_user_permissions")
        self.assertTrue(view.__class__.__name__ == 'RemoveUserPermissionsView')


    def test_remove_permission_form_user(self):
        portal = self.layer['portal']
        portal_url = portal.absolute_url()

        portal.portal_membership.setLocalRoles(
            obj=portal.folder1,
            member_ids=[TEST_USER_ID],
            member_role="Contributor",
            reindex=True)

        portal.portal_membership.setLocalRoles(
            obj=portal.folder1.folder2,
            member_ids=[TEST_USER_ID],
            member_role="Editor",
            reindex=True)

        browser = Browser(self.layer['app'])

        # Login as test user
        browser.open(portal_url + '/login_form')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl(name='submit').click()

        browser.open(portal_url + '/folder1/remove_user_permissions')
        # Look for the right form
        self.assertIn(
            '<form method="post" action="http://nohost/plone/folder1/@@remove_user_permissions">',
            browser.contents
        )


        # Search for a user, there should be the test user
        browser.getControl(name="search_term").value = TEST_USER_ID
        browser.getControl(name="form.button.Search").click()
        self.assertIn(
            '<a href="http://nohost/plone/folder1/@@remove_user_permissions?user=test_user_1_">test_user_1_</a>',
            browser.contents
        )

        # Choose user
        browser.open('http://nohost/plone/folder1/@@remove_user_permissions?user=test_user_1_')
        # Confirm link
        self.assertIn(
            '<a class="context" href="http://nohost/plone/folder1/@@remove_user_permissions?user=test_user_1_&amp;confirmed=1">',
            browser.contents
        )
        # Abort link
        self.assertIn(
            '<a class="standalone" href="http://nohost/plone/folder1/@@remove_user_permissions">',
            browser.contents
        )

        # Confirm removal of roles for the test user
        browser.open('http://nohost/plone/folder1/@@remove_user_permissions?user=test_user_1_&amp;confirmed=1')
        # After removal, redirect to permission manager overview
        self.assertIn(
            'class="template-permission_manager',
            browser.contents)

        # Approve if user has no local roles on folder1 and folder2
        self.assertFalse(
            TEST_USER_ID in dict(portal.folder1.get_local_roles()))
        self.assertFalse(
            TEST_USER_ID in dict(portal.folder1.folder2.get_local_roles()))

    def test_remove_permission_form_group(self):
        portal = self.layer['portal']
        portal_url = portal.absolute_url()
        browser = Browser(self.layer['app'])
        TEST_GROUP_ID = 'test_group'

        # Set up a group - commit change for test browser
        portal.portal_groups.addGroup(TEST_GROUP_ID)
        transaction.commit()
        # Add locale roles to a group
        portal.folder1.manage_addLocalRoles(TEST_GROUP_ID, ['Contributor',])
        portal.folder1.folder2.manage_addLocalRoles(TEST_GROUP_ID, ['Editor',])

        # Login as test user
        browser.open(portal_url + '/login_form')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl(name='submit').click()

        browser.open(portal_url + '/folder1/remove_user_permissions')
        # Look for the right form
        self.assertIn(
            '<form method="post" action="http://nohost/plone/folder1/@@remove_user_permissions">',
            browser.contents
        )

        # Search for for the test goup
        browser.getControl(name="search_term").value = TEST_GROUP_ID
        browser.getControl(name="form.button.Search").click()
        self.assertIn(
            '<a href="http://nohost/plone/folder1/@@remove_user_permissions?user=test_group">test_group</a>',
            browser.contents
        )

        # Choose group
        browser.open('http://nohost/plone/folder1/@@remove_user_permissions?user=test_group')
        # Confirm link
        self.assertIn(
            '<a class="context" href="http://nohost/plone/folder1/@@remove_user_permissions?user=test_group&amp;confirmed=1">',
            browser.contents
        )
        # Abort link
        self.assertIn(
            '<a class="standalone" href="http://nohost/plone/folder1/@@remove_user_permissions">',
            browser.contents
        )

        # Confirm removal of roles for the test group
        browser.open('http://nohost/plone/folder1/@@remove_user_permissions?user=test_group&amp;confirmed=1')
        # After removal, redirect to permission manager overview
        self.assertIn(
            'class="template-permission_manager',
            browser.contents)

        # Approve if user has no local roles on folder1 and folder2
        self.assertFalse(
            TEST_GROUP_ID in [entry[0] for entry in portal.folder1.get_local_roles()])
        self.assertFalse(
            TEST_GROUP_ID in [entry[0] for entry in portal.folder1.folder2.get_local_roles()])
