from zope.interface import Interface

# Stop! I know what you're thinking: wouldn't it be great if we made these
# things configurable, pershaps some nice little widget in Plone to pick your
# package. People could edit *anything*. Yay!
#
# Security team says: Relax! Don't do it!
#
CUSTOMIZATIONS_PACKAGE_NAME = 'plone-customizations'
CUSTOMIZATIONS_PACKAGE_NAMESPACE = 'customizationpackage'


class ICustomizationsEditorLayer(Interface):
    """Browser layer used to indicate that collective.customizationseditor is installed
    """


class ICustomizationPackage(Interface):
    """Represents a package that can contain customisations.

    See browser/namespace.py
    """
