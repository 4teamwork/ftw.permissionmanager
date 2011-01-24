from zope.i18nmessageid import MessageFactory
import csv


permission_manager_factory = MessageFactory('ftw.permissionmanager')


class excel_ger(csv.excel):
    """Extend csv library with custem dialect excel_ger"""
    delimiter = ';'
csv.register_dialect('excel_ger', excel_ger)


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
