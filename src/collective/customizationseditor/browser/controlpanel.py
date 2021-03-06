from zope.component import getMultiAdapter
from zope.publisher.browser import BrowserView

from AccessControl import Unauthorized
from Products.Five.browser.decode import processInputs
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage

from collective.customizationseditor.interfaces import CUSTOMIZATIONS_PACKAGE_NAME


class ControlPanel(BrowserView):

    def __call__(self):
        self.setup()

        if self.update():
            return self.index()
        return ''

    def setup(self):
        self.request.response.setHeader('X-Theme-Disabled', '1')
        processInputs(self.request)

        self.customizationsPackageName = CUSTOMIZATIONS_PACKAGE_NAME
        self.portalUrl = getToolByName(self.context, 'portal_url')()
        self.jsVariables = "" % (
            )

    def update(self):
        return True

    def authorize(self):
        authenticator = getMultiAdapter((self.context, self.request), name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized

    def redirect(self, message):
        IStatusMessage(self.request).add(message)
        self.request.response.redirect("%s/@@customizations-editor" % self.portalUrl)
