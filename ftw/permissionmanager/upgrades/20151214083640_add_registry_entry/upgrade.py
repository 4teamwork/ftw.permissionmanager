from ftw.upgrade import UpgradeStep


class AddRegistryEntry(UpgradeStep):
    """Add registry entry.
    """

    def __call__(self):
        self.install_upgrade_profile()
