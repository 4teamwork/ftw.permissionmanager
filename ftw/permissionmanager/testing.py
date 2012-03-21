from zope.configuration import xmlconfig
from plone.testing import Layer
from plone.testing import zca


class FtwPermissionmanagerZCMLLayer(Layer):
    """ZCML test layer for ftw.tooltips"""

    defaultBases = (zca.ZCML_DIRECTIVES, )

    def testSetUp(self):
        self['configurationContext'] = zca.stackConfigurationContext(
        self.get('configurationContext'))

        import ftw.Permissionmanager.tests
        xmlconfig.file('tests.zcml', ftw.tooltip.tests,
            context=self['configurationContext'])

    def testTearDown(self):
        del self['configurationContext']

FTWPERMISSIONMANAGER_ZCML_LAYER = FtwPermissionmanagerZCMLLayer()
