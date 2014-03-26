from ftw.upgrade import UpgradeStep


class InstallNewIndex(UpgradeStep):

    def __call__(self):
        catalog = self.getToolByName('portal_catalog')
        catalog.addIndex('principal_with_local_roles', 'KeywordIndex')
        self.catalog_reindex_objects({'is_folderish': True},
                                     idxs=['principal_with_local_roles'])
