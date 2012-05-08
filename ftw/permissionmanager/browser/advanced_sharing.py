from zope.component import getUtilitiesFor, getUtility
from plone.registry.interfaces import IRegistry
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from plone.app.workflow.interfaces import ISharingPageRole
from plone.memoize.instance import memoize


class AdvancedSharingView(BrowserView):

    def __init__(self, *args, **kwargs):
        super(AdvancedSharingView, self).__init__(*args, **kwargs)

        self.user_selected = None
        self.user = None
        registry = getUtility(IRegistry)
        self.types = registry['ftw.permissionmanager.manage_types']

    def __call__(self, *args, **kwargs):
        self.request.set('disable_border', True)
        form = self.request.form
        self.user_selected = form.get('user', False) and True
        self.user = form.get('user', False)
        return super(AdvancedSharingView, self).__call__(*args, **kwargs)

    @memoize
    def roles(self):
        """Get a list of roles that can be managed.

        Returns a list of dics with keys:

            - id
            - title
        """
        pairs = []
        for name, utility in getUtilitiesFor(ISharingPageRole):
            pairs.append(dict(id = name, title = utility.title))

        pairs.sort(lambda x, y: cmp(x['id'], y['id']))
        return pairs

    def show_advanded_links(self):
        portal_membership = getToolByName(self.context, 'portal_membership')
        return portal_membership.checkPermission(
            'Sharing page: Delegate roles', self.context)

    @memoize
    def items(self):
        rootBrain = self.context.portal_catalog({
            'path': {
                'query': '/'.join(self.context.getPhysicalPath()),
                'depth': 0,
            },
        })[0]
        items, _index = self.brainsToItems([rootBrain])
        return items

    def brainsToItems(self, brains, index=0):
        if index > 0:
            cssClass = 'child-of-node-%i' % index
        else:
            cssClass = 'expanded'
        items = []
        contextDepth = len(self.context.getPhysicalPath())
        roleIds = [x['id'] for x in self.roles()]
        for brain in brains:
            index += 1
            # make item
            absoluteDepth = len(brain.getPath().split('/'))
            aquired = getattr(brain, 'isLocalRoleAcquired', True)
            item = {
                    'title': brain.Title,
                    'path': brain.getPath(),
                    'depth': absoluteDepth - contextDepth,
                    'cssClass': cssClass,
                    'rowid': 'node-%i' % index,
                    'isLocalRoleAcquired': aquired,
            }
            # roles
            for role in roleIds:
                item[role] = []
            if brain.get_local_roles:
                for user, roles in brain.get_local_roles:
                    if not self.user_selected or user == self.user:
                        for role in roles:
                            if role in item:
                                item[role].append(user)
            items.append(item)
            # children
            query = dict(path={
                    'query': brain.getPath(),
                    'depth': 1,
                },
                sort_on = 'getObjPositionInParent', )
            if self.types:
                query['portal_type'] = self.types
            children = self.context.portal_catalog(query)
            subItems, index = self.brainsToItems(children, index)
            items.extend(subItems)
        return items, index

    @memoize
    def users_and_groups(self):
        objectItems = self.items()
        roleIds = [x['id'] for x in self.roles()]
        userGroupMap = {}
        for item in objectItems:
            for role in roleIds:
                for user in item[role]:
                    if user not in userGroupMap:
                        userItem = self._getUserOrGroupItem(user)
                        if userItem:
                            userGroupMap[user] = userItem
                        else:
                            userGroupMap[user] = {
                                'id': user,
                                'name': user,
                                'type': 'Geloeschter Benutzer',
                            }
        # make a list
        userGroupList = userGroupMap.values()
        # sort the list by id
        userGroupList.sort(lambda a, b: cmp(a['id'], b['id']))
        return userGroupList

    def _getUserOrGroupItem(self, id_):
        item = self._getUserItem(id_)
        if item:
            return item
        item = self._getGroupItem(id_)
        if item:
            return item
        return None

    def _getUserItem(self, id_):
        user = self.context.acl_users.getUserById(id_)
        if not user:
            return None
        item = {
                'id': id_,
                'name': user.getProperty('fullname'),
                'type': 'Benutzer',
        }
        return item

    def _getGroupItem(self, id_):
        group = self.context.portal_groups.getGroupById(id_)
        if not group:
            return None
        item = {
                'id': id_,
                'name': group.getGroupTitleOrName(),
                'type': 'Gruppe',
        }
        return item
