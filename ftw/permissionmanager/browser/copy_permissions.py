from ftw.permissionmanager import permission_manager_factory as _
from ftw.permissionmanager.utils import update_security_of_objects
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getMultiAdapter


class CopyUserPermissionsView(BrowserView):

    def __init__(self, *args, **kwargs):
        super(CopyUserPermissionsView, self).__init__(*args, **kwargs)

        self.source_user = None
        self.target_user = None
        self.confirm = None

    def __call__(self, *args, **kwargs):
        self.request.set('disable_border', True)
        form = self.request.form
        self.source_user = form.get('source_user', None)
        self.target_user = form.get('target_user', None)
        self.confirm = form.get('confirm', False)
        if self.source_user and self.target_user and self.confirm:
            return self.copy_permissions()
        return super(CopyUserPermissionsView, self).__call__(*args, **kwargs)

    def search_source_user(self):
        search_term = self.request.form.get('search_source_user', False)
        return self.search_results(search_term)

    def search_target_user(self):
        search_term = self.request.form.get('search_target_user', False)
        return self.search_results(search_term)

    def search_results(self, search_term):
        if not search_term:
            return []
        results = []
        userids = []
        groupids = []
        hunter = getMultiAdapter((self.context, self.request),
                                  name='pas_search')
        # users
        users = hunter.searchUsers(fullname=search_term) + \
            hunter.searchUsers(id=search_term)
        for userinfo in users:
            userid = userinfo['userid']
            user = self.context.acl_users.getUserById(userid)
            if userid not in userids:
                results.append(dict(id=userid,
                                    title=user.getProperty(
                                    'fullname') or user.getId() or userid,
                                    type='user'))
                userids.append(userid)
        # groups
        for groupinfo in hunter.searchGroups(id=search_term):
            groupid = groupinfo['groupid']
            group = self.context.portal_groups.getGroupById(groupid)
            if groupid not in groupids:
                results.append(dict(id=groupid,
                                    title=group.getGroupTitleOrName(),
                                    type='group'))
                groupids.append(groupid)
        return results

    def source_user_title(self):
        return self.getUserOrGroupTitle(self.source_user)

    def target_user_title(self):
        return self.getUserOrGroupTitle(self.target_user)

    def getUserOrGroupTitle(self, user):
        if not user:
            return None
        user = self.context.acl_users.getUserById(user)
        if user:
            return user.getProperty('fullname')
        group = self.context.portal_groups.getGroupById(user)
        if group:
            return group.getGroupTitleOrName()
        return ''

    def copy_permissions(self):
        brains = self.context.portal_catalog(
            path='/'.join(self.context.getPhysicalPath()))

        changed_objects = []
        for brain in brains:
            if self.source_user not in dict(brain.get_local_roles):
                continue

            obj = brain.getObject()
            local_roles = dict(obj.get_local_roles())
            existing_roles = local_roles.get(self.target_user, ())
            new_roles = tuple(set(existing_roles + local_roles.get(self.source_user, ())))
            if new_roles != existing_roles:
                changed_objects.append(obj)
                obj.manage_setLocalRoles(self.target_user, new_roles)
                obj.reindexObject(idxs=['getId'])

        IStatusMessage(self.request).addStatusMessage(
            _(u'Die Berechtigungen wurden kopiert'), type='info')

        update_security_of_objects(changed_objects)
        return self.request.RESPONSE.redirect('@@copy_user_permissions')
