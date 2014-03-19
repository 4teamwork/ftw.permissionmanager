from ftw.builder import Builder
from ftw.builder import create
from ftw.permissionmanager.testing import FTW_PERMISSIONMGR_INTEGRATION_TESTING
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase


class TestReindexObjectSecurityPatch(TestCase):

    layer = FTW_PERMISSIONMGR_INTEGRATION_TESTING

    def setUp(self):
        self.catalog = getToolByName(self.layer['portal'], 'portal_catalog')

    def _get_brain(self, obj):
        return self.catalog(path='/'.join(obj.getPhysicalPath()))[0]

    def test_if_metadata_are_up_to_date(self):
        folder = create(Builder('folder'))
        john = create(Builder('user').with_roles('Reader', on=folder))
        folder.reindexObjectSecurity()

        brain = self._get_brain(folder)

        self.assertIn((john.getId(), ('Reader', )), brain.get_local_roles)
        self.assertTrue(brain.isLocalRoleAcquired)

    def test_index_is_up_to_date(self):
        folder = create(Builder('folder'))
        john = create(Builder('user').with_roles('Reader', on=folder))
        folder.reindexObjectSecurity()

        self.assertEquals(
            1,
            len(self.catalog(principal_with_local_roles=john.getId())),
            'Expect one catalog entry')
