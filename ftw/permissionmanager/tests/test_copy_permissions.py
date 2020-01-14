from ftw.builder import Builder
from ftw.builder import create
from ftw.permissionmanager.testing import FTW_PERMISSIONMGR_FUNCTIONAL_TESTING
from ftw.testbrowser import browsing
import transaction
import unittest as unittest


class TestCopyPermissions(unittest.TestCase):

    layer = FTW_PERMISSIONMGR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def _get_brain(self, obj):
        path = '/'.join(obj.getPhysicalPath())
        return self.portal.portal_catalog({'path': {'query': path, 'depth': 0}})[0]

    @browsing
    def test_copy_permissions_from_user_to_user(self, browser):
        folder1 = create(Builder('folder').titled(u'folder1'))
        folder2 = create(Builder('folder').titled(u'folder2').within(folder1))

        create(Builder('user').named('Hugo', 'Boss'))
        folder1.manage_addLocalRoles('hugo.boss', ['Editor'])
        folder2.manage_addLocalRoles('hugo.boss', ['Contributor'])
        folder1.reindexObjectSecurity()
        folder1.reindexObject(idxs=['getId'])
        folder2.reindexObject(idxs=['getId'])

        create(Builder('user').named('Marie', 'Maroon'))

        # search source user
        browser.login().visit(self.portal, view='copy_user_permissions')
        browser.fill({'search_source_user': 'hugo.boss'}).submit()

        # choose source user
        browser.find('Boss Hugo').click()

        # search target user
        browser.fill({'search_target_user': 'marie.maroon'}).submit()

        # choose target user
        browser.find('Maroon Marie').click()

        # test confirm text
        expected_text = ['Are you sure to copy the permissions of user Boss Hugo (hugo.boss) on '
                         'object "Plone site" and all sub objects, to Maroon Marie (marie.maroon)']
        actual_text = browser.css('.text-confirm-copy').normalized_text()
        self.assertEquals(expected_text, actual_text)

        # confirm to copy permissions
        browser.css('button.context').first.click()

        # test redirection
        expected_url = 'http://nohost/plone/@@copy_user_permissions'
        self.assertEquals(expected_url, browser.url)

        # test status message
        self.assertIn('Info Die Berechtigungen wurden kopiert',
                      [node.normalized_text() for node in browser.css('.portalMessage.info')])

        # test copied permissions
        self.assertIn(('marie.maroon', ('Editor',)), folder1.get_local_roles())
        self.assertIn(('marie.maroon', ('Contributor',)), folder2.get_local_roles())

        self.assertEquals(folder1.get_local_roles(), self._get_brain(folder1).get_local_roles)
        self.assertEquals(folder2.get_local_roles(), self._get_brain(folder2).get_local_roles)

    @browsing
    def test_abort_copying_permissions(self, browser):

        folder1 = create(Builder('folder').titled(u'folder1'))
        folder2 = create(Builder('folder').titled(u'folder2').within(folder1))

        create(Builder('user').named('Hugo', 'Boss'))
        folder1.manage_addLocalRoles('hugo.boss', ['Editor'])
        folder2.manage_addLocalRoles('hugo.boss', ['Contributor'])
        folder1.reindexObjectSecurity()

        create(Builder('user').named('Marie', 'Maroon'))

        # search source user
        browser.login().visit(self.portal, view='copy_user_permissions')
        browser.fill({'search_source_user': 'hugo.boss'}).submit()

        # choose source user
        browser.find('Boss Hugo').click()

        # search target user
        browser.fill({'search_target_user': 'marie.maroon'}).submit()

        # choose target user
        browser.find('Maroon Marie').click()

        # abort copying permissions
        browser.find('No, abort').click()

        # test redirection
        expected_url = 'http://nohost/plone/@@copy_user_permissions'
        self.assertEquals(expected_url, browser.url)

        # test status message
        self.assertNotIn('Info Die Berechtigungen wurden kopiert',
                         [node.normalized_text() for node in browser.css('.portalMessage.info')])

        # test whether the permission have not been copied
        self.assertNotIn(('marie.maroon', ('Editor',)), folder1.get_local_roles())
        self.assertNotIn(('marie.maroon', ('Contributor',)), folder2.get_local_roles())

    @browsing
    def test_copy_permissions_from_group_to_group(self, browser):
        folder1 = create(Builder('folder').titled(u'folder1'))
        folder2 = create(Builder('folder').titled(u'folder2').within(folder1))

        create(Builder('group').titled('Group Oldies'))

        folder1.manage_addLocalRoles('group-oldies', ['Editor'])
        folder2.manage_addLocalRoles('group-oldies', ['Contributor'])
        folder1.reindexObjectSecurity()
        folder1.reindexObject(idxs=['getId'])
        folder2.reindexObject(idxs=['getId'])

        create(Builder('group').titled('Group Newbies'))

        # search source group
        browser.login().visit(self.portal, view='copy_user_permissions')
        browser.fill({'search_source_user': 'group-oldies'}).submit()

        # choose source group
        browser.find('Group Oldies').click()

        # search target group
        browser.fill({'search_target_user': 'group-newbies'}).submit()

        # choose target group
        browser.find('Group Newbies').click()

        # test confirm text
        expected_text = ['Are you sure to copy the permissions of user (group-oldies) on object '
                         '"Plone site" and all sub objects, to (group-newbies)']
        actual_text = browser.css('.text-confirm-copy').normalized_text()
        self.assertEquals(expected_text, actual_text)

        # confirm to copy permissions
        browser.css('button.context').first.click()

        # test redirection
        expected_url = 'http://nohost/plone/@@copy_user_permissions'
        self.assertEquals(expected_url, browser.url)

        # test status message
        self.assertIn('Info Die Berechtigungen wurden kopiert',
                      [node.normalized_text() for node in browser.css('.portalMessage.info')])

        # test copied permissions
        self.assertIn(('group-newbies', ('Editor',)), folder1.get_local_roles())
        self.assertIn(('group-newbies', ('Contributor',)), folder2.get_local_roles())

        self.assertEquals(folder1.get_local_roles(), self._get_brain(folder1).get_local_roles)
        self.assertEquals(folder2.get_local_roles(), self._get_brain(folder2).get_local_roles)

    @browsing
    def test_do_not_overwrite_existing_permissions(self, browser):
        folder1 = create(Builder('folder').titled(u'folder1'))
        folder2 = create(Builder('folder').titled(u'folder2').within(folder1))

        create(Builder('user').named('Hugo', 'Boss'))
        create(Builder('user').named('Marie', 'Maroon').with_roles('Reviewer', on=folder1))

        folder1.manage_addLocalRoles('hugo.boss', ['Editor'])
        folder2.manage_addLocalRoles('hugo.boss', ['Contributor'])
        folder1.reindexObjectSecurity()
        folder1.reindexObject(idxs=['getId'])
        folder2.reindexObject(idxs=['getId'])
        transaction.commit()

        # search source user
        browser.login().visit(self.portal, view='copy_user_permissions')
        browser.fill({'search_source_user': 'hugo.boss'}).submit()

        # choose source user
        browser.find('Boss Hugo').click()

        # search target user
        browser.fill({'search_target_user': 'marie.maroon'}).submit()

        # choose target user
        browser.find('Maroon Marie').click()

        # confirm to copy permissions
        browser.css('button.context').first.click()

        # test copied permissions
        self.assertIn(('marie.maroon', ('Reviewer', 'Editor')), folder1.get_local_roles())
        self.assertIn(('marie.maroon', ('Contributor',)), folder2.get_local_roles())
