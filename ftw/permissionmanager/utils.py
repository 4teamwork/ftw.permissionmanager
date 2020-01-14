from Acquisition import aq_chain


def update_security_of_objects(objects):
    objects = set(objects)
    for obj in objects.copy():
        parents = set(aq_chain(obj)[1:])
        if parents & objects:
            objects.remove(obj)

    for obj in objects:
        obj.reindexObjectSecurity()


def reindex_metadata(obj):
    # The standard indexing does not update catalog metadata.
    # We need to do that because we introduce security relevant
    # catalog metadata in this package.

    # In order to do that, we reindex the fast index "getId" of the
    # current context, so that we can use `update_metadata=True`.
    # We do not do that recursive because the metadata values
    # are non-recursive.

    catalog = obj._getCatalogTool()
    if catalog is None:
        return
    path = '/'.join(obj.getPhysicalPath())

    for brain in catalog.unrestrictedSearchResults(path=path):
        brain.getObject().reindexObject(idxs=['getId'])  # updates metadata
