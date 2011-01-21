from zope.i18nmessageid import MessageFactory


permission_manager_factory = MessageFactory('ftw.permissionmanager')

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
