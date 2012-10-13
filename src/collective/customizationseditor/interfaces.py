from zope.interface import Interface

class ICustomizationsEditorLayer(Interface):
    """Browser layer used to indicate that collective.customizationseditor is installed
    """

class ICustomizationPackage(Interface):
    """Represents a package that can contain customisations.

    See browser/namespace.py
    """
