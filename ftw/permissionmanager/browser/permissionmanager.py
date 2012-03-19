from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName


class PermissionManager(BrowserView):

    def __call__(self, *args, **kwargs):
        self.request.set('disable_border', True)
        portal_membership = getToolByName(self.context, 'portal_membership')
        # Redirect ro advanced_sharing view, if user has read only permission
        if not portal_membership.checkPermission(
            'Sharing page: Delegate roles', self.context):
            return self.context.restrictedTraverse('@@advanced-sharing')()

        return super(PermissionManager, self).__call__(*args, **kwargs)
