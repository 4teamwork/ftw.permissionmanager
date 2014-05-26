from ftw.upgrade import UpgradeStep
from ftw.upgrade.progresslogger import ProgressLogger
from ftw.upgrade.step import LOG


class InstallMetadata(UpgradeStep):

    def __call__(self):
        self.setup_install_profile(
            'profile-ftw.permissionmanager.upgrades:2302')
        self.update_workflow_id_metadata()

    def update_workflow_id_metadata(self):
        brains = self.catalog_unrestricted_search({}, full_objects=False)
        for brain in ProgressLogger('Reindex workflow_id metadata', brains):
            try:
                obj = self.catalog_unrestricted_get_object(brain)
            except AttributeError:
                LOG.warning('Could not get {0}'.format(brain.getPath()))
                continue

            catalog = self.getToolByName('portal_catalog')
            catalog.reindexObject(obj, idxs=['id'], update_metadata=True)
