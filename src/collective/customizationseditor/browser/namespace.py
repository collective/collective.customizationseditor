import urllib

from zope.interface import implements
from zope.component import adapts

from zope.traversing.interfaces import ITraversable
from zope.traversing.namespace import SimpleHandler

from collective.customizationseditor.interfaces import ICustomizationsEditorLayer
from collective.customizationseditor.interfaces import ICustomizationPackage

from Products.CMFPlone.interfaces import IPloneSiteRoot

from zExceptions import NotFound


class CustomizationPackage(object):
    """Transient container simulating traveral to the filesystem locaton of
    the customizations package.
    """
    implements(ICustomizationPackage)

    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent


    # TODO: Add methods useful for implementing the file operations in
    # the FileManager class. Should use pkg_resources API and provide primitives
    # like read file, write file, delete file, etc.

class CustomizationPackageTraverser(SimpleHandler):
    """The ++customizationpackage++ namespace
    """
    implements(ITraversable)
    adapts(IPloneSiteRoot, ICustomizationsEditorLayer)

    name = "customizationpackage"

    # TODO: Maybe make this more configurable, but we definitely want to be
    # very restrictive in what we allow people to access
    allowedPackages = frozenset(['plone-customizations'])

    def __init__(self, context, request=None):
        self.context = context

    def traverse(self, name, remaining):
        # Note: also fixes possible unicode problems
        name = urllib.quote(name)

        if name not in self.allowedPackages:
            raise NotFound

        # TODO: Check if package actually exists and raise NotFound if not

        return CustomizationPackage(
                name=name,
                parent=self.context,
            )
