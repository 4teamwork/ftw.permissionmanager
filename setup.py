from setuptools import setup, find_packages
import os

version = '3.0.3.dev0'
maintainer = 'Mathias Leimgruber'

tests_require = [
    'plone.app.contenttypes',
    'plone.app.testing',
    'Products.DateRecurringIndex',
    'ftw.testbrowser',
    'ftw.testing',
    'ftw.builder']

setup(name='ftw.permissionmanager',
      version=version,
      description="",
      long_description=open("README.rst").read() + "\n" + \
          open(os.path.join("docs", "HISTORY.txt")).read(),

      # Get more strings from
      # http://www.python.org/pypi?%3Aaction=list_classifiers

      classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 4.3',
        'Framework :: Plone :: 5.1',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],

      keywords='',
      author='4teamwork AG',
      author_email='mailto:info@4teamwork.ch',
      maintainer=maintainer,
      url='https://github.com/4teamwork/ftw.permissionmanager',
      license='GPL2',

      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
        'Plone',
        'setuptools',
        'Products.CMFPlone >= 4.3b',
        'ftw.upgrade',
        'ftw.profilehook',
        # -*- Extra requirements: -*-
        ],
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),

      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
