import StringIO
import csv
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.permissionmanager import permission_manager_factory as _


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
        self.structure_only = self.request.get('structure_only') and True or False
        if self.request.get('export'):
            return self.export()
        elif self.request.get('import'):
            self.startImport()
        else:
            self.recursive = True
            self.relative_paths = False
        return super(ImportExportPermissionsView, self).__call__(*args, **kwargs)

    def export(self):
        query = {}
        path = {
            'query': '/'.join(self.context.getPhysicalPath()),
        }
        if not self.recursive:
            path['depth'] = 0
        query['path'] = path
        if self.structure_only:
            query['is_folderish'] = True
        objects = [b.getObject() for b in self.context.portal_catalog(**query)]
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
        _file = self.request.get('file')
        data = _file.read().replace('\r\n', '\n').replace('\r', '\n')
        data = StringIO.StringIO(data)
        dialect = csv.Sniffer().sniff(data.readline())
        data.seek(0)
        reader = csv.DictReader(data, fieldnames=ImportExportPermissionsView.FIELDNAMES,
                            dialect=dialect)
        titles = None
        rows_imported = 0
        for row in reader:
            if not titles:
                titles = row
                continue
            if self.setPermissions(row):
                rows_imported += 1
        IStatusMessage(self.request).addStatusMessage(
            _(
                u'Es wurden ${rows_imported} Berechtigungen gesetzt.',
                mapping=dict(rows_imported=rows_imported)),
            type='info')

        self.context.reindexObjectSecurity()
        #self.context.restrictedTraverse('@@update_security')()

    def setPermissions(self, row):
        try:
            obj = self.getObjectByPath(row)
        except:
            IStatusMessage(self.request).addStatusMessage(
                _(
                    u'Objekt konnte nicht gefunden werden: ${path}',
                    mapping=dict(path=row['Path'])),
                type='error')

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
