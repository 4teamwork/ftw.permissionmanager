from Acquisition import aq_base
from logging import WARNING
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.log import log
from Products.Archetypes.utils import isFactoryContained
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.utils import getToolByName


def permissionmanager_reindexObjectSecurity(self, skip_self=False):
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
            # PATCH: Append principal_with_local_roles index to security
            # relevant indexes.
            indexes = list(self._cmf_security_indexes)
            indexes.append('principal_with_local_roles')
            # Recatalog with the same catalog uid.
            # PATCH: update_metadata=1, origin ist update_metadata=0.
            # We add get_local_roles and isLocalRoleAcquired to the metadata
            catalog.reindexObject(ob, idxs=tuple(indexes),
                                  update_metadata=1, uid=brain_path)
