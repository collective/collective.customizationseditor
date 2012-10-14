import pkg_resources
import os.path
import Globals

from zope.interface import implements
from zope.component import adapts

from zope.traversing.interfaces import ITraversable
from zope.traversing.namespace import SimpleHandler

from collective.customizationseditor.interfaces import ICustomizationsEditorLayer
from collective.customizationseditor.interfaces import ICustomizationPackage

from collective.customizationseditor.interfaces import CUSTOMIZATIONS_PACKAGE_NAME
from collective.customizationseditor.interfaces import CUSTOMIZATIONS_PACKAGE_NAMESPACE

from Products.CMFPlone.interfaces import IPloneSiteRoot

from zExceptions import NotFound, Unauthorized


class CustomizationPackage(object):
    """Transient container simulating traveral to the filesystem locaton of
    the customizations package.
    """
    implements(ICustomizationPackage)

    def __init__(self, distribution, name, parent):
        self.distribution = distribution
        self.path = distribution.location
        self.__name__ = name
        self.__parent__ = parent


class CustomizationPackageTraverser(SimpleHandler):
    """The ++customizationpackage++ namespace
    """
    implements(ITraversable)
    adapts(IPloneSiteRoot, ICustomizationsEditorLayer)

    name = CUSTOMIZATIONS_PACKAGE_NAMESPACE

    allowedPackages = frozenset([CUSTOMIZATIONS_PACKAGE_NAME])

    def __init__(self, context, request=None):
        self.context = context

    def traverse(self, name, remaining):
        if name not in self.allowedPackages:
            raise NotFound

        distribution = None

        try:
            distribution = pkg_resources.get_distribution(name)
        except pkg_resources.DistributionNotFound:
            raise NotFound

        # Maybe not a filesystem egg
        if not os.path.isdir(distribution.location):
            raise NotFound("%s is not a filesystem development egg")

        if not Globals.DevelopmentMode:
            raise Unauthorized("The package traverser is only available in development mode")

        return CustomizationPackage(
                distribution=distribution,
                name=name,
                parent=self.context,
            )
