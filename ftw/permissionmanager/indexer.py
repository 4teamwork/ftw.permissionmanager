from plone.indexer import indexer
from Products.Archetypes.interfaces import IBaseObject


@indexer(IBaseObject)
def global_get_local_roles(object):
    return object.get_local_roles()


@indexer(IBaseObject)
def isLocalRoleAcquired(object):
    if getattr(object, '__ac_local_roles_block__', None):
        return False
    return True
