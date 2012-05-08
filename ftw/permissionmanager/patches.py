from Products.Archetypes.utils import isFactoryContained
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.config import TOOL_NAME
from Products.CMFCore.interfaces import ICatalogTool
from Products.Archetypes.log import log
from logging import WARNING
from Acquisition import aq_base


def egov_reindexObjectSecurity(self, skip_self=False):
    if isFactoryContained(self):
        return
    at = getToolByName(self, TOOL_NAME, None)
    if at is None:
        return

    catalogs = [c for c in at.getCatalogsByType(self.meta_type)
                           if ICatalogTool.providedBy(c)]
    path = '/'.join(self.getPhysicalPath())

    for catalog in catalogs:
        for brain in catalog.unrestrictedSearchResults(path=path):
            brain_path = brain.getPath()
            if brain_path == path and skip_self:
                continue

            # Get the object
            if hasattr(aq_base(brain), '_unrestrictedGetObject'):
                ob = brain._unrestrictedGetObject()
            else:
                # BBB: Zope 2.7
                ob = self.unrestrictedTraverse(brain_path, None)
            if ob is None:
                # BBB: Ignore old references to deleted objects.
                # Can happen only in Zope 2.7, or when using
                # catalog-getObject-raises off in Zope 2.8
                log("reindexObjectSecurity: Cannot get %s from catalog" %
                    brain_path, level=WARNING)
                continue
            # Also append our new index
            indexes = list(self._cmf_security_indexes)
            indexes.append('get_local_roles')
            indexes.append('isLocalRoleAcquired')
            # Recatalog with the same catalog uid.
            catalog.reindexObject(ob, idxs=tuple(indexes),
                                    update_metadata=1, uid=brain_path)
