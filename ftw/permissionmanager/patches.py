def permissionmanager_reindexObjectSecurity(self, skip_self=False):
    # Execute standard object reindexing.
    self._old_reindexObjectSecurity(skip_self=skip_self)

    # The standard indexing does not update catalog metadata.
    # We need to do that because we introduce security relevant
    # catalog metadata in this package.

    # In order to do that, we reindex the fast index "getId" of the
    # current context, so that we can use `update_metadata=True`.
    # We do not do that recursive because the metadata values
    # are non-recursive.

    catalog = self._getCatalogTool()
    if catalog is None:
        return
    path = '/'.join(self.getPhysicalPath())

    for brain in catalog.unrestrictedSearchResults(path=path):
        brain.getObject().reindexObject(idxs=['getId'])  # updates metadata
