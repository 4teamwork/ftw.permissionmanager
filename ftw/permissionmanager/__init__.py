from Products.CMFCore import CMFCatalogAware
from zope.i18nmessageid import MessageFactory
import csv


permission_manager_factory = MessageFactory('ftw.permissionmanager')


class excel_ger(csv.excel):
    """Extend csv library with custem dialect excel_ger"""
    delimiter = ';'
csv.register_dialect('excel_ger', excel_ger)


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
    register_local_roles_index()


def register_local_roles_index():
    name = 'principal_with_local_roles'
    klass = CMFCatalogAware.CMFCatalogAware

    if name in klass._cmf_security_indexes:
        return

    indexes = list(klass._cmf_security_indexes)
    indexes.append(name)
    klass._cmf_security_indexes = tuple(indexes)
