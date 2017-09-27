from Acquisition import aq_inner
from itertools import chain
from plone.app.workflow import PloneMessageFactory as _
from plone.app.workflow.browser.sharing import merge_search_results
from plone.app.workflow.browser.sharing import SharingView as base
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode, getSiteEncoding
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PlonePAS.plugins.autogroup import VirtualGroup
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.i18n import translate


class SharingView(base):
    """This sharing view works a bit diffrent than the one from plone
       The search result is displayed in his own table.
       If a role is selected in search result table, the entry will be added
       to current_settings, this (kind of) saves the result for the user
    """

    # index: New integration for Plone >= 4.3.2
    # template: Backward compatibility Plone < 4.3.2
    index = template = ViewPageTemplateFile('templates/sharing.pt')

    def __call__(self, *args, **kwargs):
        self.disable_right_column()
        return super(SharingView, self).__call__(*args, **kwargs)

    def disable_right_column(self):
        self.request.set('disable_plone.rightcolumn', 1)

    def handle_form(self):
        if self.request.form.get('form.button.Save', None):
            # Clear the search form and hide the search results when the
            # sharing form is submitted.
            self.request.form.pop('search_term', None)
        return super(SharingView, self).handle_form()

    def has_manage_portal(self):
        return self.context.portal_membership.checkPermission(
            'ManagePortal',
            self.context)

    def has_local_role(self, role=''):
        local_roles = self.context.aq_explicit.get_local_roles()
        authenticated_member = \
            self.context.portal_membership.getAuthenticatedMember().id
        for userid, roles in local_roles:
            if (authenticated_member == userid and role in roles) \
                or self.has_manage_portal():
                return True
        return False


    def user_search_results(self):
        """Return search results for a query to add new users.

        Returns a list of dicts, as per role_settings().
        """

        def search_for_principal(hunter, search_term):
            registry = getUtility(IRegistry)
            fields = registry["ftw.permissionmanager.fields_to_search"]
            return merge_search_results(chain(*[hunter.searchUsers(**{field: search_term})
                for field in fields]), 'userid')

        def get_principal_by_id(user_id):
            acl_users = getToolByName(self.context, 'acl_users')
            return acl_users.getUserById(user_id)

        def get_principal_title(user, default_title):
            return user.getProperty('fullname') or user.getId() or default_title

        return self._principal_search_results(search_for_principal,
            get_principal_by_id, get_principal_title, 'user', 'userid')

    def group_search_results(self):
        """Return search results for a query to add new groups.

        Returns a list of dicts, as per role_settings().
        """

        def search_for_principal(hunter, search_term):
            return merge_search_results(chain(*[hunter.searchGroups(**{field:search_term})
                for field in ['id', 'title']]), 'groupid')

        def get_principal_by_id(group_id):
            portal_groups = getToolByName(self.context, 'portal_groups')
            return portal_groups.getGroupById(group_id)

        def get_principal_title(group, _):
            title = getattr(group, 'title', None)
            return title or group.getName()

        return self._principal_search_results(search_for_principal,
            get_principal_by_id, get_principal_title, 'group', 'groupid')

    def role_settings(self):
        """Only return current settings"""
        results = self.existing_role_settings()
        encoding = getSiteEncoding(aq_inner(self.context))
        static = {}
        index = None
        # Puts AuthenticatedUsers group to position 0
        for item in results:
            if item['id'] == 'AuthenticatedUsers':
                index = results.index(item)
                break
        if index != -1 and index is not None:
            static = results.pop(index)
        results.sort(
            lambda x, y: cmp(
                safe_unicode(x["title"], encoding).lower(),
                safe_unicode(y["title"], encoding).lower()))
        # Only show AuthenticatedUsers group users with ManagePortal
        # perission
        # XXX: This should be configurable
        if static and self.has_manage_portal():
            results.insert(0, static)
        return results

    def search_result(self):
        """Returns only the search result for the new search result table"""

        # XXX: This method is inefficient. To many interations and
        # manipulations. # If someone really understands what to do,
        # please do it.

        mtool = getToolByName(self.context, 'portal_membership')
        gtool = getToolByName(self.context, 'portal_groups')
        user_results = self.user_search_results()
        group_results = self.group_search_results()
        current_settings = user_results + group_results

        requested = self.request.form.get('entries', [])

        # Remove real/saved roles from requested
        for item in self.existing_role_settings():
            index = None
            for r_item in requested:
                if item['id'] == r_item['id']:
                    index = requested.index(r_item)
                    break
            if index is not None:
                requested.pop(index)

        if requested is not None:
            knownroles = [r['id'] for r in self.roles()]
            settings = {}
            result_like_settings = {}
            for entry in requested:
                roles = []
                roles_for_settings = {}
                for r in knownroles:
                    if entry.get('role_%s' % r, False):
                        roles.append(r)
                        roles_for_settings[r] = True
                    else:
                        roles_for_settings[r] = False
                    settings[(entry['id'], entry['type'])] = roles
                # Add requested entries to current_settings if there is one or
                #  more roles selected
                # This is kind a temporary storage for search results.
                # It allows you to do multible search queries and you will not
                # lose allready selected roles for user/groups
                if roles and not self.request.get('form.button.Save', None):
                    # get group title or user fullname
                    if entry['type'] == 'user':
                        member = mtool.getMemberById(entry['id'])
                        title = '%s' % (
                            member.getProperty('fullname', entry['id']))
                    else:
                        group = gtool.getGroupById(entry['id'])
                        title = group.getGroupTitleOrName()
                    result_like_settings = {
                        'id': entry['id'],
                        'type': entry['type'],
                        'title': title,
                        'roles': roles_for_settings}

                    # Add or update settings
                    updated = False
                    for given_entry in current_settings:
                        if result_like_settings['id'] == given_entry['id']:
                            given_entry.update(result_like_settings)
                            updated = True
                            break
                    if not updated:
                        current_settings.append(result_like_settings)
            for entry in current_settings:
                desired_roles = settings.get(
                    (entry['id'], entry['type']),
                    None)

                if desired_roles is None:
                    continue
                for role in entry["roles"]:
                    if entry["roles"][role] in [True, False]:
                        entry["roles"][role] = role in desired_roles

        encoding = getSiteEncoding(aq_inner(self.context))
        current_settings.sort(
            lambda x, y: cmp(
                safe_unicode(x["title"], encoding).lower(),
                safe_unicode(y["title"], encoding).lower()))

        return current_settings

    def _principal_search_results(self,
                                  search_for_principal,
                                  get_principal_by_id,
                                  get_principal_title,
                                  principal_type,
                                  id_key):
        """Return search results for a query to add new users or groups.

        Returns a list of dicts, as per role_settings().

        Arguments:
            search_for_principal -- a function that takes an IPASSearchView and
                a search string. Uses the former to search for the latter and
                returns the results.
            get_principal_by_id -- a function that takes a user id and returns
                the user of that id
            get_principal_title -- a function that takes a user and a default
                title and returns a human-readable title for the user. If it
                can't think of anything good, returns the default title.
            principal_type -- either 'user' or 'group', depending on what kind
                of principals you want
            id_key -- the key under which the principal id is stored in the
                dicts returned from search_for_principal
        """
        context = self.context

        translated_message = translate(_(u"Search for user or group"),
                                       context=self.request)
        search_term = self.request.form.get('search_term', None)
        if not search_term or search_term == translated_message:
            return []

        existing_principals = set([p['id'] for p in self.existing_role_settings()
                                if p['type'] == principal_type])
        empty_roles = dict([(r['id'], False) for r in self.roles()])
        info = []

        hunter = getMultiAdapter((context, self.request), name='pas_search')
        for principal_info in search_for_principal(hunter, search_term):
            principal_id = principal_info[id_key]
            if principal_id not in existing_principals:
                principal = get_principal_by_id(principal_id)
                roles = empty_roles.copy()

                if principal is None and principal_type == 'group':
                    """ Discovery not implemented. Use a virtual group. """
                    principal = VirtualGroup(
                        principal_info['id'],
                        principal_info['title'] if 'title' in principal_info else '',
                        principal_info['description'] if 'description' in principal_info else '')

                for r in principal.getRoles():
                    if r in roles:
                        roles[r] = 'global'
                login = principal.getUserName()
                if principal_type == 'group':
                    login = None
                info.append(dict(id = principal_id,
                                 title = get_principal_title(principal,
                                                             principal_id),
                                 login = login,
                                 type = principal_type,
                                 roles = roles))
        return info
