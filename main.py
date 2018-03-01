
# [START app]
from __future__ import print_function
import logging
import os
import hashlib
import re
import googleapiclient.discovery
import base64
import sys
import google.oauth2.id_token
import google.auth.transport.requests
import requests_toolbelt.adapters.appengine

from werkzeug.exceptions import Unauthorized
from oauth2client.client import GoogleCredentials

# [START imports]
from flask import Flask, request, jsonify
# [END imports]

# [START create_app]
app = Flask(__name__)
# [END create_app]

# Use the App Engine Requests adapter. This makes sure that Requests uses URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()
HTTP_REQUEST = google.auth.transport.requests.Request()

# Require all requests to include this API key - keep it a secret to your application
REQUIRED_API_KEY = "<PUT_SOME_RANDOM_API_KEY_THAT_YOU_REQUIRE_HERE>"

# Your Google Cloud Platform project ID
PROJECT_ID = "<YOUR_APPENGINE_APP_ID_HERE>"

# Lists keys in the "global" location.
LOCATION = "global"

# Instantiate the client
credentials = GoogleCredentials.get_application_default()
kms_client = googleapiclient.discovery.build('cloudkms', 'v1', credentials=credentials)

# Set the required scopes to access the Key Management Service API
# @see https://developers.google.com/identity/protocols/application-default-credentials#callingruby
# kms_client.authorization = Google::Auth.get_application_default(
#   "https://www.googleapis.com/auth/cloud-platform"
# )

PARENT = 'projects/{}/locations/{}'.format(PROJECT_ID, LOCATION)

KEYRING_NAME = "<KMS_KEYRING_NAME>"
KEY_ID = "<KMS_KEY_ID>"


# The resource name of the location associated with the Key rings
KEY_NAME = "{}/keyRings/{}/cryptoKeys/{}".format(PARENT, KEYRING_NAME, KEY_ID)

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

class AuthService:

  def __init__(self):
    self.line_ending_stripper = re.compile(r"={1,2}\n?$")

  def validate_api_key(self, request_args):
    if request_args.get('key', None) != REQUIRED_API_KEY:
      raise Unauthorized('Invalid API Key')

  def auth_info_from_verified_claims(self, claims):
    if not claims:
      raise Unauthorized('Not authorized')

    if 'sub' not in claims or len(claims['sub']) == 0:
      raise Unauthorized('Not authorized')

    if 'groups' not in claims or len(claims['groups']) == 0:
      user_groups = []
    else:
      # Split the comma-separated list and remove any blank entries
      user_groups = list(filter(None, claims['groups'].split(",")))

    return {
      'id': claims['sub'],
      'groups': user_groups
    }

  def auth_info(self, request_headers):
    id_token = request_headers['Authorization'].split(' ').pop()
    try:
      claims = google.oauth2.id_token.verify_firebase_token(id_token, HTTP_REQUEST)
    except ValueError:
      raise Unauthorized('Not authorized')

    return self.auth_info_from_verified_claims(claims)

  def generate_random_key(self):
    password = b"<USE_A_SECURE_RANDOM_PASSWORD_HERE>"
    salt = os.urandom(16)
    iterations = 20000
    key_len = 16
    raw_key = hashlib.pbkdf2_hmac('sha1', password, salt, iterations, key_len)
    ascii_key = self.line_ending_stripper.sub("", base64.b64encode(raw_key).decode('ascii'))
    return ascii_key


  def encrypt_key(self, owner_id, ascii_key):
    kms_request = kms_client.projects().locations().keyRings().cryptoKeys().encrypt(name=KEY_NAME, body={
      "plaintext": base64.b64encode(owner_id + "|" + ascii_key).decode('ascii')
    })
    response = kms_request.execute()

    encrypted_key = response['ciphertext']

    clean_encrypted_key = self.line_ending_stripper.sub("", encrypted_key).replace("/", "_").replace("+", "-")

    return clean_encrypted_key

  def group_id_from_key_owner(self, key_owner):
    if key_owner.startswith('g:'):
      # Strip off the prefix to get the group ID
      group_id = key_owner[2:]
      eprint("Key group ID is " + group_id)
      return group_id
    else:
      eprint("Personal key detected")
      return None

  def authorised_for_key(self, key_owner, auth):
    user_id = auth['id']

    # See if this is a user key or a group key
    key_group = self.group_id_from_key_owner(key_owner)

    if key_group is None:
      if key_owner != user_id:
        eprint("Auth failure comparing user IDs {} with {}".format(key_owner, user_id))
        return False
    else:
      if len(key_group) == 0:
        eprint("Blank group ID found in key")
        return False

      elif key_group not in auth['groups']:
        eprint("Auth failure comparing group ID {} with {}".format(key_owner, auth['groups']))
        return False

    return True

  def get_verified_key(self, encrypted_key, auth):
    decrypt_request = kms_client.projects().locations().keyRings().cryptoKeys().decrypt(name=KEY_NAME, body={
      "ciphertext": encrypted_key
    })
    response = decrypt_request.execute()

    components = base64.b64decode(response['plaintext']).split("|", 2)

    if len(components) > 1:
      if not self.authorised_for_key(components[0], auth):
        raise Unauthorized('Not authorized')

    key = self.line_ending_stripper.sub("", components[-1])

    return key


auth_service = AuthService()

# [START key]
@app.route('/key', methods=['POST'])
def generate_key():
  auth_service.validate_api_key(request.args)
  auth = auth_service.auth_info(request.headers)
  user_id = auth['id']

  ascii_key = auth_service.generate_random_key()

  return jsonify({
    "key": ascii_key,
    "encrypted":  auth_service.encrypt_key(user_id, ascii_key)
  })
# [END key]

# [START groupkey]
@app.route('/groupkey', methods=['POST'])
def generate_group_keys():
  auth_service.validate_api_key(request.args)

  group_id = request.args['group']

  if len(group_id) == 0:
    raise InvalidUsage('Missing parameter "group"')

  ascii_key = auth_service.generate_random_key()

  return jsonify({
    "key": ascii_key,
    "encrypted": auth_service.encrypt_key('g:' + group_id, ascii_key)
  })
# [END groupkey]

# [START decrypt]
@app.route('/decrypt')
def decrypt():
  auth_service.validate_api_key(request.args)
  auth = auth_service.auth_info(request.headers)

  return jsonify({
    "key": auth_service.get_verified_key(request.args['value'], auth)
  })
# [END decrypt]

@app.errorhandler(500)
def server_error(e):
  # Log the error and stacktrace.
  logging.exception('An error occurred during a request.')
  return 'An internal error occurred.', 500
# [END app]
