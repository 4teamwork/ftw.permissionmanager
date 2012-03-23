from ftw.permissionmanager.testing import FTW_PERMISSIONMANAGER_INTEGRATION_TESTING, TEST_USER_ID_2
import unittest2 as unittest
from plone.app.testing import TEST_USER_NAME, TEST_USER_ID, login, logout
from ftw.permissionmanager.browser.sharing import SharingView


class TestRemovePermissions(unittest.TestCase):
    """Sharing is well tested by Plone, so just our customized methods"""

    layer = FTW_PERMISSIONMANAGER_INTEGRATION_TESTING


    def setUp(self):
        # Set up a new user
        portal = self.layer['portal']

        portal.portal_membership.setLocalRoles(
            obj=portal.folder1,
            member_ids=[TEST_USER_ID],
            member_role="Contributor",
            reindex=True)
        portal.folder1.reindexObjectSecurity()

    def test_has_manager_role(self):
        """TEST_USER_ID has manager role from testsetup"""
        portal = self.layer['portal']
        view = SharingView(portal.folder1, portal.folder1.REQUEST)
        self.assertTrue(view.has_manage_portal())

    def test_has_local_role(self):
        portal = self.layer['portal']
        view = SharingView(portal.folder1, portal.folder1.REQUEST)

        # As TEST_USER_ID
        self.assertTrue(view.has_local_role())
        logout()
        login(portal, TEST_USER_ID_2)
        # As TEST_USER_ID_2
        self.assertFalse(view.has_local_role())
        logout()
        login(portal, TEST_USER_NAME)

    def test_role_settings(self):
        """TEST_USER_ID should be Contributor"""
        portal = self.layer['portal']
        view = SharingView(portal.folder1, portal.folder1.REQUEST)
        for entry in view.role_settings():
            if entry['id'] == TEST_USER_ID:
                break
        self.assertTrue(entry['roles']['Contributor'])

