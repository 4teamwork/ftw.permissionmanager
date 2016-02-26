from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.utils import isFactoryContained
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.utils import getToolByName


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
    if isFactoryContained(self):
        return
    at = getToolByName(self, TOOL_NAME, None)
    if at is None:
        return

    catalogs = [catalog for catalog in at.getCatalogsByType(self.meta_type)
                if ICatalogTool.providedBy(catalog)]

    for catalog in catalogs:
        catalog.reindexObject(self, idxs=['getId'], update_metadata=True)
