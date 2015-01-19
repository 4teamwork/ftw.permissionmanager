from Acquisition import aq_inner
from plone.app.workflow.browser.sharing import SharingView as base
from plone.app.workflow.interfaces import ISharingPageRole
from plone.memoize.instance import memoize
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode, getSiteEncoding
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtilitiesFor


class SharingView(base):
    """This sharing view works a bit diffrent than the one from plone
       The search result is displayed in his own table.
       If a role is selected in search result table, the entry will be added
       to current_settings, this (kind of) saves the result for the user
    """

    # index: New integration for Plone >= 4.3.2
    # template: Backward compatibility Plone < 4.3.2
    index = template = ViewPageTemplateFile('templates/sharing.pt')

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
