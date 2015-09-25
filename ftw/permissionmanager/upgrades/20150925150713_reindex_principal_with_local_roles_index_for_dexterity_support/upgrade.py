from ftw.upgrade import UpgradeStep


class ReindexPrincipalWithLocalRolesIndexForDexteritySupport(UpgradeStep):
    """Reindex principal with local roles index for dexterity support.
    """

    def __call__(self):
        self.install_upgrade_profile()
        self.catalog_rebuild_index('principal_with_local_roles')
