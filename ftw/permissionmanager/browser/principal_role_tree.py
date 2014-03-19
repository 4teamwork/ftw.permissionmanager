from plone.app.workflow.interfaces import ISharingPageRole
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import BadRequest
from zope.component import queryUtility
from zope.i18n import translate
import json


def get_friendly_role_name(names, request):
    friendly_names = []

    for name in names:
        utility = queryUtility(ISharingPageRole, name=name)
        if utility is None:
            friendly_names.append(name)
        else:
            friendly_names.append(translate(utility.title, context=request))
    return ', '.join(friendly_names)


class PrincipalRoleTree(BrowserView):

    def __call__(self):
        return self.index()


class SearchPrincipals(BrowserView):

    def __init__(self, context, request):
        super(SearchPrincipals, self).__init__(context, request)
        self.search_term = None

    def __call__(self):
        self.search_term = self.request.get('search_term', None)

        if not self.search_term:
            raise BadRequest('No search_term found.')

        if len(self.search_term) <= 2:
            return json.dumps([])

        principals = self.search_principals()
        return json.dumps(self._format_result(principals))

    def search_principals(self):
        principals = self.search_principals_by_fullname()
        principals = principals + self.search_principals_by_userid()
        return principals

    def search_principals_by_fullname(self):
        users = getToolByName(self.context, "acl_users")
        return users.searchUsers(fullname=self.search_term)

    def search_principals_by_userid(self):
        users = getToolByName(self.context, "acl_users")
        return users.searchUsers(id=self.search_term)

    def _format_result(self, principals):
        ids = []
        formatted = []
        for principal in principals:
            userid = principal['userid']
            if principal['userid'] not in ids:
                fullname = principal['title']

                # search for userids returns the userid also as title
                if userid == fullname:
                    mtool = getToolByName(self.context, 'portal_membership')
                    member = mtool.getMemberById(userid)
                    fullname = member and member.getProperty(
                        'fullname', userid) or userid
                data = {'id': userid, 'text': '{0} ({1})'.format(fullname,
                                                                 userid)}
                formatted.append(data)
                ids.append(userid)

        formatted.sort(key=lambda item: item['text'])
        return formatted


class BuildPrincipalRoleTree(BrowserView):

    item_template = ViewPageTemplateFile('item_template.pt')

    def __init__(self, context, request):
        super(BuildPrincipalRoleTree, self).__init__(context, request)
        self.principalid = None
        self.groupids = []

    def __call__(self):
        mtool = getToolByName(self.context, 'portal_membership')
        gtool = getToolByName(self.context, 'portal_groups')

        principalid = self.request.get('principalid', None)

        if not principalid:
            return ''

        self.principalid = principalid

        member = mtool.getMemberById(self.principalid)
        if member:
            groups = gtool.getGroupsByUserId(self.principalid)
            self.groupids = [group.getId() for group in groups]

        return self.render_tree(self.build_tree()['children'])

    def render_tree(self, children=[], level=1):
        output = ''
        for node in children:
            output += '<li class="treeItem visualNoMarker">\n'
            output += self.item_template(node=node)
            children = node.get('children', [])
            if len(children):
                output += \
                    '<ul class="level%d">\n%s\n</ul>\n' % (
                        level, self.render_tree(children, level + 1))
            output += '</li>\n'
        return output

    def build_query(self):
        query = {}
        principals = [self.principalid] + self.groupids

        query['principal_with_local_roles'] = principals

        query['path'] = {'query': '/'.join(self.context.getPhysicalPath()),
                         'depth': -1}
        return query

    def build_tree(self):
        items = {}
        root_path = '/'.join(self.context.getPhysicalPath())
        query = self.build_query()
        catalog = getToolByName(self.context, 'portal_catalog')
        results = self.context.portal_catalog(**query)

        items[root_path] = {'children': []}

        for item in results:
            self._insert_item(root_path, items, item)

        # Insert parents and add missing brains if necessary
        paths = items.keys()
        paths.reverse()
        for path in paths:
            if path == root_path:
                continue

            parent_path = '/'.join(path.split('/')[:-1])
            node = items[path]

            if node.get('item', None) is None:
                item = catalog.unrestrictedSearchResults(
                    {'path': {'query': path, 'depth': 0}})[0]

                node['item'] = item

            if parent_path in items:
                items[parent_path]['children'].append(node)
            else:
                items[parent_path] = {'children': [node]}

            if parent_path == root_path:
                continue

        return items[root_path]

    def _insert_item(self, root_path, items, item):
        item_path = item.getPath()
        itemPhysicalPath = item_path.split('/')
        parent_path = '/'.join(itemPhysicalPath[:-1])

        if item_path in items:
            return
        new_node = {'item': item,
                    'children': [],
                    'user_roles': self.get_user_roles(item),
                    'group_roles': self.get_group_roles(item)}

        if items.get(parent_path):
            items[parent_path]['children'].append(new_node)
        else:
            items[parent_path] = {'children': [new_node]}

            while True:
                parent_path = '/'.join(parent_path.split('/')[:-1])
                if parent_path == root_path:
                    break
                items[parent_path] = {'children': []}

    def get_user_roles(self, brain):
        local_roles = brain.get_local_roles
        for principal, roles in local_roles:
            if principal == self.principalid:
                return get_friendly_role_name(roles, self.request)
        return ''

    def get_group_roles(self, brain):
        local_roles = brain.get_local_roles
        group_roles = []

        for groupid in self.groupids:
            for principal, roles in local_roles:
                if principal == groupid:
                    gtool = getToolByName(self.context, 'portal_groups')
                    gtitle = gtool.getGroupById(groupid).getProperty(
                        'title',
                        groupid)
                    group_roles.append({'title': gtitle,
                                        'roles': get_friendly_role_name(
                                            roles,
                                            self.request)})
        return group_roles
