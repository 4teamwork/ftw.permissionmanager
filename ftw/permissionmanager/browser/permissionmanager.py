import StringIO
import csv
from zope.component import getMultiAdapter
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.workflow.browser.sharing import SharingView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.permissionmanager import permission_manager_factory as _

# extend csv library with custem dialect excel_ger
class excel_ger(csv.excel):
    delimiter = ';'
csv.register_dialect('excel_ger', excel_ger)


class PermissionManager(BrowserView):

    def __call__(self, *args, **kwargs):
        self.request.set('disable_border', True)
        return super(PermissionManager, self).__call__(*args, **kwargs)


class RemoveUserPermissionsView(SharingView):

    template = ViewPageTemplateFile('remove_user_permissions.pt')

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
        hunter = getMultiAdapter((self.context, self.request), name='pas_search')
        # users
        users = hunter.searchUsers(fullname=search_term) + \
            hunter.searchUsers(id=search_term)
        for userinfo in users:
            userid = userinfo['userid']
            user = self.context.acl_users.getUserById(userid)
            results.append(dict(id = userid,
                             title = user.getProperty('fullname') or user.getId() or userid,
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
        brains = self.context.portal_catalog(path='/'.join(self.context.getPhysicalPath()))
        for brain in brains:
            if self.user in dict(brain.get_local_roles).keys():
                obj = brain.getObject()
                obj.manage_delLocalRoles((self.user, ))
        self.context.restrictedTraverse('@@update_security')()



class CopyUserPermissionsView(BrowserView):

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
        hunter = getMultiAdapter((self.context, self.request), name='pas_search')
        # users
        users = hunter.searchUsers(fullname=search_term) + \
            hunter.searchUsers(id=search_term)
        for userinfo in users:
            userid = userinfo['userid']
            user = self.context.acl_users.getUserById(userid)
            results.append(dict(id = userid,
                             title = user.getProperty('fullname') or user.getId() or userid,
                             type = 'user'))
        # groups
        for groupinfo in hunter.searchGroups(id=search_term):
            groupid = groupinfo['groupid']
            group = self.context.portal_groups.getGroupById(groupid)
            results.append(dict(id = groupid,
                             title = group.getGroupTitleOrName(),
                             type = 'group'))
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
        brains = self.context.portal_catalog(path='/'.join(self.context.getPhysicalPath()))
        for brain in brains:
            for user, roles in dict(brain.get_local_roles).items():
                obj = brain.getObject()
                if user==self.source_user:
                    obj.manage_setLocalRoles(self.target_user, roles)
        IStatusMessage(self.request).addStatusMessage(
            _(u'Die Berechtigungen wurden kopiert'), type='info')
        
        self.context.restrictedTraverse('@@update_security')()
        return self.request.RESPONSE.redirect('@@copy_user_permissions')


class ImportExportPermissionsView(BrowserView):

    ROLES = ['Administrator', 'Anonymous', 'Authenticated', 'Contributor',
                  'Editor', 'Manager', 'Member', 'Owner', 'Publisher',
                  'Reader', 'Reviewer', ]
    FIELDNAMES = ['Name', 'Userid', 'Title'] + ROLES + ['Path']
    READONLY = ('Name', 'Title', )

    def __call__(self, *args, **kwargs):
        self.request.set('disable_border', True)
        # Export
        self.recursive = self.request.get('recursive') and True or False
        self.relative_paths = self.request.get('relative_paths') and True or False
        if self.request.get('export'):
            return self.export()
        elif self.request.get('import'):
            self.startImport()
        else:
            self.recursive = True
            self.relative_paths = False
        return super(ImportExportPermissionsView, self).__call__(*args, **kwargs)

    def export(self):
        path = {
            'query': '/'.join(self.context.getPhysicalPath()),
        }
        if not self.recursive:
            path['depth'] = 0
        objects = [b.getObject() for b in self.context.portal_catalog({'path': path})]
        self.file = StringIO.StringIO()
        writer = csv.DictWriter(self.file,
                                fieldnames=ImportExportPermissionsView.FIELDNAMES,
                                dialect='excel_ger')
        labels = ['%s%s' % (l, l in ImportExportPermissionsView.READONLY and ' (RO)' or '')
                  for l in ImportExportPermissionsView.FIELDNAMES]
        writer.writerow(dict(zip(ImportExportPermissionsView.FIELDNAMES, labels)))
        for obj in objects:
            self.export_object(writer, obj)
        self.file.seek(0)
        data = self.file.read()
        #
        self.request.RESPONSE.setHeader('Content-Type', 'text/csv; charset=utf-8')
        filename = '%s-permissions.csv' % self.context.id
        self.request.RESPONSE.setHeader('Content-disposition', 'attachment; filename=%s' % filename)
        return data

    def export_object(self, writer, obj):
        path = '/'.join(obj.getPhysicalPath())
        if self.relative_paths:
            contextPath = '/'.join(self.context.getPhysicalPath())
            path = '...%s' % path[len(contextPath):]
        for user, roles in obj.get_local_roles():
            row = {
                'Name': user,
                'Userid': user,
                'Title': obj.Title(),
                'Path': path,
            }
            for role in roles:
                if role in ImportExportPermissionsView.ROLES:
                    row[role] = 'X'
            writer.writerow(row)

    def startImport(self):
        file = self.request.get('file')
        file.readline()
        dialect = csv.Sniffer().sniff(file.readline())
        file.seek(0)
        reader = csv.DictReader(file, fieldnames=ImportExportPermissionsView.FIELDNAMES,
                            dialect=dialect)
        titles = None
        rows_imported = 0
        for row in reader:
            if not titles:
                titles = row
                continue
            if self.setPermissions(row):
                rows_imported += 1
        info(self.context.request,
             'Es wurden %i Berechtigungen gesetzt.' % rows_imported)
        self.context.restrictedTraverse('@@update_security')()

    def setPermissions(self, row):
        try:
            obj = self.getObjectByPath(row)
        except:
            error(self.context.request,
                  'Objekt konnte nicht gefunden werden: %s' % row['Path'])
            return False
        user = row['Userid']
        roles = []
        for role in ImportExportPermissionsView.ROLES:
            if len(row[role])>0:
                roles.append(role)
        if len(roles)>0:
            obj.manage_setLocalRoles(user, roles)
        else:
            obj.manage_delLocalRoles((user, ))
        return True

    def getObjectByPath(self, row):
        path = row['Path']
        if path.startswith('...'):
            # relative paths
            path = path[len('.../'):]
        obj = self.context.restrictedTraverse(path)
        return obj
