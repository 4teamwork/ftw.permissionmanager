from zope.component import getMultiAdapter
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.workflow.browser.sharing import SharingView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.permissionmanager import permission_manager_factory as _


class RemoveUserPermissionsView(SharingView):

    template = ViewPageTemplateFile('remove_user_permissions.pt')

    def __init__(self, *args, **kwargs):
        super(RemoveUserPermissionsView, self).__init__(*args, **kwargs)

        self.search = None
        self.user_selected = None
        self.user = None
        self.confirmed = None

    def __call__(self, *args, **kwargs):
        self.request.set('disable_border', True)
        form = self.request.form
        self.search = form.get('search_user', False)
        self.user_selected = form.get('user', False) and True
        self.user = form.get('user', False)
        self.confirmed = form.get('confirmed', False) and True
        if self.confirmed:
            self.removePermissions()
            IStatusMessage(self.request).addStatusMessage(
                _(
                    u'Die Berechtigungen wurden erfolgreich entfernt.'),
                    type='info')
            return self.request.RESPONSE.redirect('@@permission_manager')
        return self.template()

    def search_results(self):
        search_term = self.request.form.get('search_term', None)
        if not search_term:
            return []
        results = []
        hunter = getMultiAdapter((self.context, self.request),
                                 name='pas_search')
        # users
        users = hunter.searchUsers(fullname=search_term) + \
            hunter.searchUsers(id=search_term)
        for userinfo in users:
            userid = userinfo['userid']
            user = self.context.acl_users.getUserById(userid)
            results.append(dict(id = userid,
                             title = user.getProperty(
                                 'fullname') or user.getId() or userid,
                             type = 'user'))
        # groups
        for groupinfo in hunter.searchGroups(id=search_term):
            groupid = groupinfo['groupid']
            group = self.context.portal_groups.getGroupById(groupid)
            results.append(dict(id = groupid,
                             title = group.getGroupTitleOrName(),
                             type = 'group'))
        return results

    def getUserOrGroupTitle(self):
        if not self.user:
            return None
        user = self.context.acl_users.getUserById(self.user)
        if user:
            return user.getProperty('fullname')
        group = self.context.portal_groups.getGroupById(self.user)
        if group:
            return group.getGroupTitleOrName()
        return ''

    def removePermissions(self):
        brains = self.context.portal_catalog(
            path='/'.join(self.context.getPhysicalPath()))
        for brain in brains:
            if self.user in dict(brain.get_local_roles).keys():
                obj = brain.getObject()
                obj.manage_delLocalRoles((self.user, ))
        self.context.reindexObjectSecurity()
        #self.context.restrictedTraverse('@@update_security')()
