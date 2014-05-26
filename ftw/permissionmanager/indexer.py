from Products.Archetypes.interfaces import IBaseObject
from Products.CMFCore.utils import getToolByName
from plone.indexer import indexer


@indexer(IBaseObject)
def global_get_local_roles(object):
    return object.get_local_roles()


@indexer(IBaseObject)
def principal_with_local_roles(obj):
    return [user_roles[0] for user_roles in obj.get_local_roles()]


@indexer(IBaseObject)
def isLocalRoleAcquired(object):
    if getattr(object, '__ac_local_roles_block__', None):
        return False
    return True


@indexer(IBaseObject)
def workflow_id(obj):
    wftool = getToolByName(obj, 'portal_workflow')
    workflows = wftool.getWorkflowsFor(obj)

    if len(workflows) == 0:
        return None

    return workflows[0].id
