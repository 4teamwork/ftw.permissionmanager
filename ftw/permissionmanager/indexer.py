from plone.indexer import indexer
from Products.Archetypes.interfaces import IBaseObject


@indexer(IBaseObject)
def global_get_local_roles(object):
    return object.get_local_roles()