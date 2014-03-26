from ftw.builder import Builder
from ftw.builder import create
from ftw.permissionmanager.testing import FTW_PERMISSIONMGR_INTEGRATION_TESTING
from unittest2 import TestCase
from zExceptions import BadRequest
from zope.component import queryMultiAdapter
import json


class TestPrincipalRoleTreeUserSearch(TestCase):

    layer = FTW_PERMISSIONMGR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_raise_badrequest_if_no_search_param_given(self):
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='principal_role_tree_search')

        with self.assertRaises(BadRequest):
            view()

    def test_return_empty_result_if_search_term_is_too_short(self):
        self.portal.REQUEST.set('search_term', 'aa')
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='principal_role_tree_search')

        self.assertEquals('[]', view(), 'Expect an empty result.')

    def test_search_user_by_fullname(self):
        create(Builder('user'))
        self.portal.REQUEST.set('search_term', 'Doe')
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='principal_role_tree_search')

        self.assertEquals(1,
                          len(json.loads(view())),
                          'Expect one entry')

    def test_search_user_by_id(self):
        create(Builder('user'))
        self.portal.REQUEST.set('search_term', 'john.doe')
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='principal_role_tree_search')

        self.assertEquals(1,
                          len(json.loads(view())),
                          'Expect one entry')

    def test_search_result_format(self):
        john = create(Builder('user'))
        john2 = create(Builder('user').named('John', 'Doe2'))

        self.portal.REQUEST.set('search_term', 'Doe')
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='principal_role_tree_search')

        text1 = '{0} ({1})'.format(john.getProperty('fullname'), john.getId())
        text2 = '{0} ({1})'.format(john2.getProperty('fullname'),
                                   john2.getId())
        self.assertEquals(
            [{u'id': john.getId(), u'text': text1},
             {u'id': john2.getId(), u'text': text2}],
            json.loads(view()),
            'Expect to find two users in json parsable format.')

    def test_search_term_with_umlauts(self):
        john = create(Builder('user').named('J\xc3\xb6hn', 'Doe2'))

        self.portal.REQUEST.set('search_term', 'J\xc3\xb6hn')
        view = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                 name='principal_role_tree_search')

        text1 = u'{0} ({1})'.format(
            john.getProperty('fullname').decode('utf-8'),
            john.getId())
        self.assertEquals(
            [{u'id': john.getId(), u'text': text1}],
            json.loads(view()),
            'Expect to find one user with umlauts')
