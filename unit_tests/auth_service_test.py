import unittest
from main import AuthService
from main import REQUIRED_API_KEY

#from google.appengine.api import users
from google.appengine.ext import testbed

from werkzeug.exceptions import Unauthorized

USER_ID = 'user123456'
GROUP_ID = 'group1234'

class ValidateApiKeyTestCase(unittest.TestCase):
  # [START setup]
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.auth_service = AuthService()
  # [END setup]

  def tearDown(self):
    self.testbed.deactivate()

  # [START test]
  def testValidKey(self):
    self.auth_service.validate_api_key({ 'key': REQUIRED_API_KEY })
  # [END test]

  # [START test]
  def testInvalidKey(self):
    with self.assertRaises(Unauthorized) as context:
      self.auth_service.validate_api_key({ 'key': 'I like cheese' })
  # [END test]
# [END ValidateApiKeyTestCase]

class AuthInfoTestCase(unittest.TestCase):
  # [START setup]
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.auth_service = AuthService()
  # [END setup]

  def tearDown(self):
    self.testbed.deactivate()

  # [START test]
  def testValidUser(self):
    claims = { 'sub': USER_ID }
    auth_info = self.auth_service.auth_info_from_verified_claims(claims)
    self.assertEqual(auth_info['id'], USER_ID)
    self.assertEqual(auth_info['groups'], [])
  # [END test]

  # [START test]
  def testInvalidUser(self):
    with self.assertRaises(Unauthorized) as context:
      auth_info = self.auth_service.auth_info_from_verified_claims({ })
  # [END test]

  # [START test]
  def testValidGroups(self):
    claims = { 'sub': USER_ID, 'groups': ',group123,group456,' }
    auth_info = self.auth_service.auth_info_from_verified_claims(claims)
    self.assertEqual(auth_info['id'], USER_ID)
    self.assertEqual(auth_info['groups'], ['group123', 'group456'])
  # [END test]

  # [START test]
  def testBlankGroups(self):
    claims = { 'sub': USER_ID, 'groups': ',,' }
    auth_info = self.auth_service.auth_info_from_verified_claims(claims)
    self.assertEqual(auth_info['id'], USER_ID)
    self.assertEqual(auth_info['groups'], [])
  # [END test]
# [END AuthInfoTestCase]

class GenerateRandomKeyTestCase(unittest.TestCase):
  # [START setup]
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.auth_service = AuthService()
  # [END setup]

  def tearDown(self):
    self.testbed.deactivate()

  # [START test]
  def testGenerateRandomKey(self):
    # Check that a key is generated of the expected length
    key = self.auth_service.generate_random_key()
    self.assertEqual(len(key), 22)

    # Check that a subsequent call generates a different key
    key2 = self.auth_service.generate_random_key()
    self.assertNotEqual(key, key2)
  # [END test]
# [END GenerateRandomKeyTestCase]

class KeyOwnerTestCase(unittest.TestCase):
  # [START setup]
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.auth_service = AuthService()
  # [END setup]

  def tearDown(self):
    self.testbed.deactivate()

  # [START test]
  def testGroupIdFromGroupKey(self):
    self.assertEqual(self.auth_service.group_id_from_key_owner('g:' + GROUP_ID), GROUP_ID)
    self.assertEqual(self.auth_service.group_id_from_key_owner('g:gp4567'), 'gp4567')
  # [END test]

  # [START test]
  def testGroupIdFromPersonalKey(self):
    self.assertEqual(self.auth_service.group_id_from_key_owner(USER_ID), None)
  # [END test]

  # [START test]
  def testUserAuthorisedForPersonalKey(self):
    self.assertTrue(self.auth_service.authorised_for_key(USER_ID, { 'id': USER_ID}))
  # [END test]

  # [START test]
  def testUserUnauthorisedForAnothersKey(self):
    self.assertFalse(self.auth_service.authorised_for_key(USER_ID, { 'id': USER_ID + 'a' }))
  # [END test]

  # [START test]
  def testUserAuthorisedForGroupKey(self):
    self.assertTrue(self.auth_service.authorised_for_key('g:' + GROUP_ID, { 'id': USER_ID, 'groups': [GROUP_ID] }))
  # [END test]

  # [START test]
  def testUserUnauthorisedForOtherGroupKey(self):
    self.assertFalse(self.auth_service.authorised_for_key('g:' + GROUP_ID, { 'id': USER_ID, 'groups': ['gp4567'] }))
  # [END test]

  # [START test]
  def testUserUnauthorisedForBlankGroupKey(self):
    self.assertFalse(self.auth_service.authorised_for_key('g:', { 'id': USER_ID, 'groups': ['gp4567'] }))
  # [END test]

# [END KeyOwnerTestCase]


if __name__ == '__main__':
  unittest.main()