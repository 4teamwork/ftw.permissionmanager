from ftw.builder import Builder
from ftw.builder import create
from ftw.permissionmanager.browser import principal_role_tree
from ftw.permissionmanager.indexer import principal_with_local_roles
from ftw.permissionmanager.testing import FTW_PERMISSIONMGR_FUNCTIONAL_TESTING
from ftw.testbrowser import browsing
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase
from zope.component import queryMultiAdapter
import transaction


class TestBuildPrincipalRoleTree(TestCase):

    layer = FTW_PERMISSIONMGR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_principal_with_local_roles_index(self):
        folder = create(Builder('folder'))
        john = create(Builder('user').with_roles('Reader', on=folder))

        self.assertEquals([john.getId(), 'test_user_1_'],
                          principal_with_local_roles(folder)())

    def test_principal_with_local_roles_index_query(self):
        folder = create(Builder('folder'))
        john = create(Builder('user').with_roles('Reader', on=folder))
        folder.reindexObject()
        catalog = getToolByName(self.portal, 'portal_catalog')
        result = catalog(principal_with_local_roles=[john.getId()])

        self.assertEquals(1,
                          len(result),
                          'Expect one entry')
        self.assertEquals(result[0].getPath(),
                          '/'.join(folder.getPhysicalPath()))

    def test_empty_result_if_no_principal_is_set(self):
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='build_principal_role_tree')

        self.assertEquals('', view())

    def _create_structure(self):
        self.folder = create(Builder('folder'))
        self.a = create(Builder('folder').titled('a').within(self.folder))
        self.a1 = create(Builder('folder').titled('a1').within(self.a))
        self.b = create(Builder('folder').titled('b').within(self.folder))
        self.b1 = create(Builder('folder').titled('b1').within(self.b))
        self.b11 = create(Builder('folder').titled('b11').within(self.b1))

    def test_build_only_branches_with_local_roles(self):
        self._create_structure()
        john = create(Builder('user').with_roles('Reader', on=self.b11))
        self.b11.reindexObject()

        self.portal.REQUEST.set('principalid', john.getId())
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='build_principal_role_tree')
        view()
        tree = view.build_tree()['children']

        level1 = tree[0]
        self.assertEquals('/'.join(self.folder.getPhysicalPath()),
                          level1['item'].getPath())

        level2 = level1['children'][0]
        self.assertEquals('/'.join(self.b.getPhysicalPath()),
                          level2['item'].getPath())

        level3 = level2['children'][0]
        self.assertEquals('/'.join(self.b1.getPhysicalPath()),
                          level3['item'].getPath())

        level4 = level3['children'][0]
        self.assertEquals('/'.join(self.b11.getPhysicalPath()),
                          level4['item'].getPath())

    def test_build_branch_with_nested_local_roles(self):
        self._create_structure()
        john = create(Builder('user')
                      .with_roles('Reader', on=self.b11)
                      .with_roles('Contributor', on=self.b))
        self.b11.reindexObject()
        self.b.reindexObject()

        self.portal.REQUEST.set('principalid', john.getId())
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='build_principal_role_tree')

        view()
        tree = view.build_tree()['children']

        level1 = tree[0]
        self.assertEquals('/'.join(self.folder.getPhysicalPath()),
                          level1['item'].getPath())

        level2 = level1['children'][0]
        self.assertEquals('/'.join(self.b.getPhysicalPath()),
                          level2['item'].getPath())

        level3 = level2['children'][0]
        self.assertEquals('/'.join(self.b1.getPhysicalPath()),
                          level3['item'].getPath())

        level4 = level3['children'][0]
        self.assertEquals('/'.join(self.b11.getPhysicalPath()),
                          level4['item'].getPath())

    def test_build_only_branches_with_local_roles_from_b(self):
        self._create_structure()
        john = create(Builder('user').with_roles('Reader', on=self.b11))
        self.b11.reindexObject()

        self.portal.REQUEST.set('principalid', john.getId())
        view = queryMultiAdapter((self.b, self.b.REQUEST),
                                 name='build_principal_role_tree')
        view()
        tree = view.build_tree()['children']

        level1 = tree[0]
        self.assertEquals('/'.join(self.b1.getPhysicalPath()),
                          level1['item'].getPath())

        level2 = level1['children'][0]
        self.assertEquals('/'.join(self.b11.getPhysicalPath()),
                          level2['item'].getPath())

    def test_build_tree_with_multiple_branches(self):
        self._create_structure()
        john = create(Builder('user')
                      .with_roles('Reader', on=self.b11)
                      .with_roles('Contributor', on=self.a1))
        self.b11.reindexObject()
        self.a1.reindexObject()

        self.portal.REQUEST.set('principalid', john.getId())
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='build_principal_role_tree')

        view()
        tree = view.build_tree()['children']

        level1 = tree[0]
        self.assertEquals('/'.join(self.folder.getPhysicalPath()),
                          level1['item'].getPath())

        level2a = level1['children'][0]
        self.assertEquals('/'.join(self.a.getPhysicalPath()),
                          level2a['item'].getPath())

        level2b = level1['children'][1]
        self.assertEquals('/'.join(self.b.getPhysicalPath()),
                          level2b['item'].getPath())

        level3a = level2a['children'][0]
        self.assertEquals('/'.join(self.a1.getPhysicalPath()),
                          level3a['item'].getPath())

    def test_build_tree_with_group_memberships(self):
        self._create_structure()
        john = create(Builder('user'))
        group = create(Builder('group')
                       .titled('Group')
                       .with_members(john))

        self.a1.manage_setLocalRoles(group.getId(), ['Contributor'])
        self.a1.reindexObject()

        self.portal.REQUEST.set('principalid', john.getId())
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='build_principal_role_tree')

        view()
        tree = view.build_tree()['children']

        level1 = tree[0]
        self.assertEquals('/'.join(self.folder.getPhysicalPath()),
                          level1['item'].getPath())

        level2 = level1['children'][0]
        self.assertEquals('/'.join(self.a.getPhysicalPath()),
                          level2['item'].getPath())

        level3 = level2['children'][0]
        self.assertEquals('/'.join(self.a1.getPhysicalPath()),
                          level3['item'].getPath())

    @browsing
    def test_build_branch_with_local_roles_HTML(self, browser):
        self._create_structure()
        john = create(Builder('user').with_roles('Reader', on=self.b11))
        self.b11.reindexObject()
        transaction.commit()

        data = {'principalid': john.getId()}
        browser.login().visit(self.portal,
                              data=data,
                              view='build_principal_role_tree')

        self.assertEquals('level1',
                          browser.css('ul')[0].attrib['class'],
                          'Expect a level1')
        self.assertEquals('level2',
                          browser.css('ul')[1].attrib['class'],
                          'Expect a level2')
        self.assertEquals('level3',
                          browser.css('ul')[2].attrib['class'],
                          'Expect a level3')

        self.assertTrue(
            browser.css('[href="{0}"]'.format(self.folder.absolute_url())),
            'Expecrt to find the following url {0}'.format(
                self.folder.absolute_url()))
        self.assertTrue(
            browser.css('[href="{0}"]'.format(self.b.absolute_url())),
            'Expecrt to find the following url {0}'.format(
                self.b.absolute_url()))
        self.assertTrue(
            browser.css('[href="{0}"]'.format(self.b1.absolute_url())),
            'Expecrt to find the following url {0}'.format(
                self.b1.absolute_url()))
        self.assertTrue(
            browser.css('[href="{0}"]'.format(self.b11.absolute_url())),
            'Expecrt to find the following url {0}'.format(
                self.b11.absolute_url()))

    @browsing
    def test_build_tree_branch_with_local_roles_HTML_only(self, browser):
        self._create_structure()
        john = create(Builder('user').with_roles('Reader', on=self.b11))
        self.b11.reindexObject()
        transaction.commit()

        data = {'principalid': john.getId()}
        browser.login().visit(self.portal,
                              data=data,
                              view='build_principal_role_tree')

        self.assertFalse(
            browser.css('[href="{0}"]'.format(self.a.absolute_url())),
            'Expecrt NOT to find the following url {0}'.format(
                self.a.absolute_url()))
        self.assertFalse(
            browser.css('[href="{0}"]'.format(self.a1.absolute_url())),
            'Expecrt NOT to find the following url {0}'.format(
                self.a1.absolute_url()))

    @browsing
    def test_item_is_marked_as_not_acquired(self, browser):
        self._create_structure()
        john = create(Builder('user').with_roles('Reader', on=self.b11))
        self.b11.reindexObject()

        setattr(self.b1, '__ac_local_roles_block__', True)
        self.b1.reindexObject()
        transaction.commit()

        data = {'principalid': john.getId()}
        browser.login().visit(self.portal,
                              data=data,
                              view='build_principal_role_tree')

        self.assertEquals(self.b1.Title(),
                          browser.css('div.not-acquired a').first.text)

    @browsing
    def test_empty_result(self, browser):
        self._create_structure()

        data = {'principalid': 'inexistingid'}
        browser.login().visit(self.portal,
                              data=data,
                              view='build_principal_role_tree')

        self.assertEquals(u'No results found', browser.contents)

    def test_get_friendly_role_name_translates_if_utility_is_registered(self):
        self.assertEquals(
            'Can add, Can edit',
            principal_role_tree.get_friendly_role_name(
                ['Contributor', 'Editor'], '', self.portal.REQUEST))

    def test_get_friendly_role_name_does_not_translate(self):
        self.assertEquals(
            'Baar, Foo',
            principal_role_tree.get_friendly_role_name(
                ['Foo', 'Baar'], '', self.portal.REQUEST))

    @browsing
    def test_translated_roles_are_displayed_in_tree(self, browser):
        self._create_structure()
        john = create(Builder('user')
                      .with_roles('Reader', on=self.b11)
                      .with_roles('Contributor', on=self.a1))
        self.b11.reindexObject()
        self.a1.reindexObject()
        transaction.commit()

        data = {'principalid': john.getId()}
        browser.login().visit(self.portal,
                              data=data,
                              view='build_principal_role_tree')
        self.assertEquals('Can add', browser.css('.UserRoles')[0].text)
        self.assertEquals('Can view', browser.css('.UserRoles')[1].text)

    def test_get_user_roles(self):
        folder = create(Builder('folder'))
        john = create(Builder('user').with_roles('Reader', on=folder))
        folder.reindexObject()
        catalog = getToolByName(self.portal, 'portal_catalog')

        result = catalog(principal_with_local_roles=[john.getId()])
        self.portal.REQUEST.set('principalid', john.getId())
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='build_principal_role_tree')

        view()
        self.assertEquals('Can view', view.get_user_roles(result[0]))

    def test_get_group_roles(self):
        folder = create(Builder('folder'))
        john = create(Builder('user'))
        group = create(Builder('group')
                       .titled('Group')
                       .with_members(john))
        folder.manage_setLocalRoles(group.getId(), ['Contributor'])
        folder.reindexObject()

        catalog = getToolByName(self.portal, 'portal_catalog')
        result = catalog(principal_with_local_roles=[group.getId()])

        self.portal.REQUEST.set('principalid', john.getId())
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='build_principal_role_tree')

        view()
        self.assertEquals([{'title': 'Group', 'roles': 'Can add'}],
                          view.get_group_roles(result[0]))

    @browsing
    def test_build_tree_shows_nested_local_roles(self, browser):
        self._create_structure()
        john = create(Builder('user')
                      .with_roles('Reader', on=self.b11)
                      .with_roles('Reader', on=self.b))
        self.b11.reindexObject()
        self.b.reindexObject()
        transaction.commit()

        data = {'principalid': john.getId()}
        browser.login().visit(self.portal,
                              data=data,
                              view='build_principal_role_tree')

        self.assertEquals('Can view',
                          browser.css('.level1 .UserRoles').first.text)
        self.assertEquals('Can view',
                          browser.css('.level3 .UserRoles').first.text)

    def test_item_template(self):
        self._create_structure()
        john = create(Builder('user').with_roles('Reader', on=self.b11))
        self.b11.reindexObject()

        self.portal.REQUEST.set('principalid', john.getId())
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='build_principal_role_tree')
        view()
        tree = view.build_tree()['children']

        level1 = tree[0]
        self.assertEquals('folder', level1['normalized_portaltype'])
