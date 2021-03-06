from ftw.builder.content import register_dx_content_builders
from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles, TEST_USER_ID, TEST_USER_NAME, login
from plone.testing import z2
from zope.configuration import xmlconfig


TEST_USER_ID_2 = '_test_user_2_'
TEST_USER_PW_2 = 'secret'
TEST_GROUP_ID = 'test_group'
TEST_GROUP_ID_2 = 'test_group_2'


class FtwPermissionmanagerLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '</configure>',
            context=configurationContext)

        z2.installProduct(app, 'ftw.permissionmanager')
        z2.installProduct(app, 'Products.DateRecurringIndex')

    def setUpPloneSite(self, portal):
        # Install into Plone site using portal_setup
        applyProfile(portal, 'ftw.permissionmanager:default')
        applyProfile(portal, 'plone.app.contenttypes:default')
        register_dx_content_builders(force=True)

        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)
        # Create one folder with one item
        portal.invokeFactory('Folder', 'folder1', title='Folder1')
        portal.folder1.invokeFactory('Folder', 'folder2', title='Folder2')

        # Add a new user
        portal.portal_registration.addMember(TEST_USER_ID_2, TEST_USER_PW_2)


FTW_PERMISSIONMANAGER_FIXTURE = FtwPermissionmanagerLayer()
FTW_PERMISSIONMGR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_PERMISSIONMANAGER_FIXTURE, ),
    name="ftw.permissionmanager:Integration")


FTW_PERMISSIONMGR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FTW_PERMISSIONMANAGER_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="ftw.permissionmanager:Functional")
