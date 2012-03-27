from zope.component import getMultiAdapter
from ftw.permissionmanager.testing import (
    FTW_PERMISSIONMANAGER_INTEGRATION_TESTING,
    TEST_USER_ID_2)
from plone.app.testing import TEST_USER_ID
import unittest2 as unittest
from plone.app.workflow.interfaces import ISharingPageRole
from zope.component import getUtilitiesFor
import StringIO


class TestCopyPermissions(unittest.TestCase):

    layer = FTW_PERMISSIONMANAGER_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        # Create document with TEST_USER_ID
        portal.folder1.folder2.invokeFactory(
            'Document', 'document1', title='Document 1')

        # Give TEST_USER_ID_2 some roles
        portal.portal_membership.setLocalRoles(
            obj=portal.folder1.folder2,
            member_ids=[TEST_USER_ID_2],
            member_role="Reader",
            reindex=True)

        portal.portal_membership.setLocalRoles(
            obj=portal.folder1.folder2.document1,
            member_ids=[TEST_USER_ID_2],
            member_role="Editor",
            reindex=True)

    def test_copy_permission_view(self):
        portal = self.layer['portal']
        view = getMultiAdapter(
            (portal.folder1, portal.folder1.REQUEST),
            name="import_export_permissions")
        self.assertTrue(view.__name__ == 'import_export_permissions')

    def test_get_roles(self):
        portal = self.layer['portal']
        view = getMultiAdapter(
            (portal.folder1, portal.folder1.REQUEST),
            name="import_export_permissions")

        roles = view.get_roles()
        for name, utility in getUtilitiesFor(ISharingPageRole):
            self.assertTrue(name in roles)

    def test_export_structure(self):
        portal = self.layer['portal']
        # set up request
        request = portal.folder1.REQUEST
        request.set('recursive', '1')
        request.set('relative_paths', '')
        request.set('structure_only', '')

        view = getMultiAdapter(
            (portal.folder1, request),
            name="import_export_permissions")
        view()
        data = view.export()
        roles = view.get_roles()
        # first row contains headers
        head = data.split('\r\n')[0].split(';')
        self.assertEqual(head[0], 'Name (RO)')
        self.assertEqual(head[1], 'Userid')
        self.assertEqual(head[2], 'Title (RO)')
        self.assertEqual(head[-1], 'Path')
        for role in roles:
            self.assertTrue(role in head)

        # All records should have the same len as the head
        for record in data.split('\r\n')[1:-1]:
            self.assertTrue(len(head) == len(record.split(';')))


    def test_export_data(self):
        portal = self.layer['portal']
        # set up request
        request = portal.folder1.REQUEST
        request.set('recursive', '1')
        request.set('relative_paths', '')
        request.set('structure_only', '')

        view = getMultiAdapter(
            (portal.folder1, request),
            name="import_export_permissions")
        view()
        data = view.export()
        head = data.split('\r\n')[0].split(';')

        # TEST_USER_ID ist Owner of folder1, folder2 and document1
        for line in data.split('\r\n')[1:-1]:
            record = line.split(';')
            if record[1] == TEST_USER_ID:
                index = head.index('Owner')
                self.assertEqual(
                    record[index], 'X')

        # TEST_USER_ID_2 has Reader role folder2
        for line in data.split('\r\n')[1:-1]:
            record = line.split(';')
            if record[1] == TEST_USER_ID:
                continue
            if record[1] == TEST_USER_ID_2 and record[-1] == '/plone/folder1/folder2':
                index = head.index('Reader')
                self.assertEqual(
                    record[index], 'X')
            elif record[1] == TEST_USER_ID_2 and record[-1] == '/plone/folder1/folder2/document1':
                index = head.index('Editor')
                self.assertEqual(
                    record[index], 'X')

    def test_export_structure_only(self):
        portal = self.layer['portal']
        # set up request
        request = portal.folder1.REQUEST
        request.set('export', '1')
        request.set('recursive', '1')
        request.set('relative_paths', '')
        request.set('structure_only', '1')

        view = getMultiAdapter(
            (portal.folder1, request),
            name="import_export_permissions")
        view()
        data = view.export()
        for line in data.split('\r\n')[1:-1]:
            record = line.split(';')
            self.assertFalse('document1' in record[-1]) # Path


    def test_export_relative_path(self):
        portal = self.layer['portal']
        # set up request
        request = portal.folder1.REQUEST
        request.set('export', '1')
        request.set('recursive', '1')
        request.set('relative_paths', '1')
        request.set('structure_only', '')

        view = getMultiAdapter(
            (portal.folder1, request),
            name="import_export_permissions")
        view()
        data = view.export()
        for line in data.split('\r\n')[1:-1]:
            record = line.split(';')
            self.assertTrue(record[-1].startswith('...')) # Path

    def test_export_not_recursiv(self):
        portal = self.layer['portal']
        # set up request
        request = portal.folder1.REQUEST
        request.set('export', '1')
        request.set('recursive', '')
        request.set('relative_paths', '')
        request.set('structure_only', '')

        view = getMultiAdapter(
            (portal.folder1, request),
            name="import_export_permissions")
        view()
        data = view.export()
        for line in data.split('\r\n')[1:-1]:
            record = line.split(';')
            self.assertTrue(record[-1] == '/plone/folder1') # Path

    def test_import_permissions(self):
        # First do a export
        portal = self.layer['portal']
        # set up request
        request = portal.folder1.REQUEST

        view = getMultiAdapter(
            (portal.folder1, request),
            name="import_export_permissions")
        view()
        data = view.export()
        head = data.split('\r\n')[0].split(';')
        # Change permission - set TEST_USER_ID_2 as Owner of folder2 and
        # docuement1
        new_records = []
        for line in data.split('\r\n')[1:-1]:
            record = line.split(';')
            if record[1] == TEST_USER_ID_2:
                index = head.index('Owner')
                new_record = record
                new_record.pop(index)
                new_record.insert(index, 'X')
                new_records.append(';'.join(new_record))
        data += '\r\n'.join(new_records)

        # Prepare import
        request.set('import', '1')
        request.set('file', StringIO.StringIO(data))
        view = getMultiAdapter(
            (portal.folder1, request),
            name="import_export_permissions")
        view()
        self.assertIn(
            'Owner',
            portal.folder1.folder2.get_local_roles_for_userid(TEST_USER_ID_2))
        self.assertIn(
            'Owner',
            portal.folder1.folder2.document1.get_local_roles_for_userid(TEST_USER_ID_2))
