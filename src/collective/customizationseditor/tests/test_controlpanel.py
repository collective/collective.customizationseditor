import unittest2 as unittest

from collective.customizationseditor.testing import THEMING_FUNCTIONAL_TESTING
from plone.testing.z2 import Browser

from plone.app.testing import setRoles, TEST_USER_ID

import Globals
import os.path

from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD

class TestControlPanel(unittest.TestCase):

    layer = THEMING_FUNCTIONAL_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        import transaction
        transaction.commit()

        self.portal = portal
        self.browser = Browser(self.layer['app'])

        handleErrors = self.browser.handleErrors
        try:
            self.browser.handleErrors = False
            self.browser.open(portal.absolute_url() + '/login_form')
            self.browser.getControl(name='__ac_name').value = TEST_USER_NAME
            self.browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
            self.browser.getControl(name='submit').click()
        finally:
            self.browser.handleErrors = handleErrors

    def goto_controlpanel(self):
        self.browser.open(self.portal.absolute_url() + '/@@customizations-editor')
