Introduction
============

Make permission management easier in Plone.

Provides several new permission / role management views:

- A sitemap like, filterable permission overview.
- Remove user/group permission recursively.
- Copy existing permission/role settings from one to another user.
- Exports/imports user/group permissions/roles recursively.

  - Export only structure (folderish types).
  - Export using relative paths.

- A better sharing view:

  - Search for users.
- Temporary stores your selection over multiple search operations.


Usage
-----

- Add ``ftw.permissionmanager`` to your buildout configuration:

::

    [instance]
    eggs +=
        ftw.permissionmanager

- Install the generic import profile.

- Configure the types that should be visible in the recursive sharing view by setting it in the registry.
  You can do this configuring it in ``portal_registry`` or by adding a ``registry.xml`` to your
  generic setup profile::

    <registry>

        <record name="ftw.permissionmanager.manage_types">
            <value>
                <element>Folder</element>
                <element>Document</element>
            </value>
        </record>

    </registry>



Links
=====

- Main github project repository: https://github.com/4teamwork/ftw.permissionmanager
- Issue tracker: https://github.com/4teamwork/ftw.permissionmanager/issues
- Package on pypi: http://pypi.python.org/pypi/ftw.permissionmanager
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.permissionmanager

Copyright
=========

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.permissionmanager`` is licensed under GNU General Public License, version 2.

.. image:: https://cruel-carlota.pagodabox.com/0aedf121b182f20d668ecc65c6741f4d
   :alt: githalytics.com
   :target: http://githalytics.com/4teamwork/ftw.permissionmanager
