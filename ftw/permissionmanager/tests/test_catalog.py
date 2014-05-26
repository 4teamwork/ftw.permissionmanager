from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.permissionmanager.testing import FTW_PERMISSIONMGR_INTEGRATION_TESTING
from unittest2 import TestCase


class TestCatalog(TestCase):
    layer = FTW_PERMISSIONMGR_INTEGRATION_TESTING

    def get_metadata_for(self, obj):
        catalog = getToolByName(obj, 'portal_catalog')
        rid = catalog.getrid('/'.join(obj.getPhysicalPath()))
        return catalog.getMetadataForRID(rid)

    def test_workflow_id_metadata(self):
        wftool = getToolByName(self.layer['portal'], 'portal_workflow')
        wftool.setChainForPortalTypes(['Document'], 'plone_workflow')

        obj = create(Builder('document'))
        self.assertDictContainsSubset(
            {'workflow_id': 'plone_workflow'},
            self.get_metadata_for(obj))

    def test_workflow_id_metadata_is_None_when_no_workflow_configured(self):
        obj = create(Builder('document'))
        self.assertDictContainsSubset(
            {'workflow_id': None},
            self.get_metadata_for(obj))
