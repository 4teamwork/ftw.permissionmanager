from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from zExceptions import BadRequest
import json


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
