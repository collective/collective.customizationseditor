from setuptools import setup, find_packages
import os

version = '1.0a1'

setup(name='collective.customizationseditor',
      version=version,
      description="Provides a safe and easy way to edit filesystem Plone customisations through the web",
      long_description=open("README.txt").read() + "\n\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='plone diazo xdv deliverance theme transform xslt',
      author='Franco Pellegrini and Martin Aspeli',
      author_email='optilude@gmail.com',
      url='http://pypi.python.org/pypi/collective.customizationseditor',
      license='GPL',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.resourceeditor',
          'plone.reload',
          'Products.CMFPlone',
          'zope.traversing',
          'plone.app.controlpanel',
      ],
      extras_require={
        'test': ['plone.app.testing'],
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
