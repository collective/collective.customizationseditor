from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import applyProfile

from zope.configuration import xmlconfig
from plone.app.testing.layers import IntegrationTesting
from plone.app.testing.layers import FunctionalTesting

class CustomizationsEditor(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        pass

    def setUpPloneSite(self, portal):
        # install into the Plone site
        applyProfile(portal, 'collective.customizationseditor:default')

THEMING_FIXTURE = CustomizationsEditor()
THEMING_INTEGRATION_TESTING = IntegrationTesting(bases=(THEMING_FIXTURE,), name="CustomizationsEditor:Integration")
THEMING_FUNCTIONAL_TESTING = FunctionalTesting(bases=(THEMING_FIXTURE,), name="CustomizationsEditor:Functional")
