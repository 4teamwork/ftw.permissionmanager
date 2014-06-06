from ftw.permissionmanager import permission_manager_factory as _
from ftw.permissionmanager.treeifier import Treeify
from plone.app.workflow.interfaces import ISharingPageRole
from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import BadRequest
from zope.component import queryUtility
from zope.i18n import translate
from zope.i18nmessageid import Message
import json
import pkg_resources


try:
    pkg_resources.get_distribution('ftw.lawgiver')
except pkg_resources.DistributionNotFound:
    LAWGIVER_INSTALLED = False
else:
    LAWGIVER_INSTALLED = True
    from ftw.lawgiver.utils import translate_role_for_workflow


def get_friendly_role_name(names, workflow_id, request):
    friendly_names = []

    for name in names:
        if LAWGIVER_INSTALLED:
            title = translate(
                translate_role_for_workflow(workflow_id, name),
                context=request)
            if isinstance(title, Message):
                title = translate(title, context=request)
            friendly_names.append(title)
            continue

        utility = queryUtility(ISharingPageRole, name=name)
        if utility is None:
            friendly_names.append(name)
        else:
            friendly_names.append(translate(utility.title, context=request))
    friendly_names.sort()
    return ', '.join(friendly_names)


class PrincipalRoleTree(BrowserView):

    def __call__(self):
        return self.index()


class SearchPrincipals(BrowserView):

    def __init__(self, context, request):
        super(SearchPrincipals, self).__init__(context, request)
        self.search_term = None

    def __call__(self):
        self.search_term = self.request.get('search_term', '')

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

                # It depends on the mood of plone whether the fullname is utf8
                # encoded or not.
                if not isinstance(fullname, unicode):
                    fullname = fullname.decode('utf-8')
                data = {u'id': userid, 'text': u'{0} ({1})'.format(fullname,
                                                                   userid)}
                formatted.append(data)
                ids.append(userid)

        formatted.sort(key=lambda item: item['text'])
        return formatted


class BuildPrincipalRoleTree(BrowserView):

    item_template = ViewPageTemplateFile('templates/item_template.pt')

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

        tree = self.build_tree()
        if not tree:
            return translate(_(u'text_no_result', default=u'No results found'),
                             context=self.request)

        else:
            return self.render_tree(tree['children'])

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
        query['sort_on'] = 'getObjPositionInParent'
        query['path'] = {'query': '/'.join(self.context.getPhysicalPath()),
                         'depth': -1}
        return query

    def build_tree(self):
        root_path = '/'.join(self.context.getPhysicalPath())
        brains = self.context.portal_catalog(**self.build_query())

        if not brains:
            return []

        tree = Treeify(brains, root_path, self.node_updater)
        return tree(self.context)

    def node_updater(self, brain, node):
        normalizer = queryUtility(IIDNormalizer)
        node['item'] = brain
        node['user_roles'] = self.get_user_roles(brain)
        node['group_roles'] = self.get_group_roles(brain)
        node['normalized_portaltype'] = normalizer.normalize(brain.portal_type)

    def get_user_roles(self, brain):
        local_roles = brain.get_local_roles
        for principal, roles in local_roles:
            if principal == self.principalid:
                return get_friendly_role_name(roles,
                                              brain.workflow_id,
                                              self.request)
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
                                            brain.workflow_id,
                                            self.request)})
        return group_roles
