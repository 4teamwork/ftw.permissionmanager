from Acquisition import aq_inner
from zope.component import getUtilitiesFor
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from plone.app.workflow.interfaces import ISharingPageRole
from plone.memoize.instance import memoize


class AdvancedSharingView(BrowserView):

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
        context = aq_inner(self.context)
        portal_membership = getToolByName(context, 'portal_membership')

        pairs = []

        for name, utility in getUtilitiesFor(ISharingPageRole):
            permission = utility.required_permission
            if permission is None or portal_membership.checkPermission(permission, context):
                pairs.append(dict(id = name, title = utility.title))

        pairs.sort(lambda x, y: cmp(x['id'], y['id']))
        return pairs

    @memoize
    def items(self):
        rootBrain = self.context.portal_catalog({
            'path': {
                'query': '/'.join(self.context.getPhysicalPath()),
                'depth': 0,
            },
        })[0]
        items, index = self.brainsToItems([rootBrain])
        return items

    def brainsToItems(self, brains, index=0):
        if index>0:
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
            item = {
                    'title': brain.Title,
                    'path': brain.getPath(),
                    'depth': absoluteDepth - contextDepth,
                    'cssClass': cssClass,
                    'rowid': 'node-%i' % index,
            }
            # roles
            for role in roleIds:
                item[role] = []
            if brain.get_local_roles:
                for user, roles in brain.get_local_roles:
                    if not self.user_selected or user==self.user:
                        for role in roles:
                            if item.has_key(role):
                                item[role].append(user)
            items.append(item)
            # children
            children = self.context.portal_catalog({
                'path': {
                    'query': brain.getPath(),
                    'depth': 1,
                },
                'sort_on': 'getObjPositionInParent',
            })
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
                    if not userGroupMap.has_key(user):
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

    def _getUserOrGroupItem(self, id):
        item = self._getUserItem(id)
        if item:
            return item
        item = self._getGroupItem(id)
        if item:
            return item
        return None

    def _getUserItem(self, id):
        user = self.context.acl_users.getUserById(id)
        if not user:
            return None
        item = {
                'id': id,
                'name': user.getProperty('fullname'),
                'type': 'Benutzer',
        }
        return item

    def _getGroupItem(self, id):
        group = self.context.portal_groups.getGroupById(id)
        if not group:
            return None
        item = {
                'id': id,
                'name': group.getGroupTitleOrName(),
                'type': 'Gruppe',
        }
        return item

