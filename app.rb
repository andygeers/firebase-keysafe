#  Copyright 2017 Andy Geers. All rights reserved.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

# [START app]
require "sinatra"
require "google/apis/cloudkms_v1"
require "openssl"

# Your Google Cloud Platform project ID
project_id = "prayermate-auth-service"

# Lists keys in the "global" location.
location = "global"

# Instantiate the client
Cloudkms   = Google::Apis::CloudkmsV1 # Alias the module
kms_client = Cloudkms::CloudKMSService.new

# Set the required scopes to access the Key Management Service API
# @see https://developers.google.com/identity/protocols/application-default-credentials#callingruby
kms_client.authorization = Google::Auth.get_application_default(
  "https://www.googleapis.com/auth/cloud-platform"
)

parent = "projects/#{project_id}/locations/#{location}"

keyring_name = "<KMS_KEYRING_NAME>"
key_id = "<KMS_KEY_ID>"

# The resource name of the location associated with the Key rings
key_name = "#{parent}/keyRings/#{keyring_name}/cryptoKeys/#{key_id}"

class AuthorizationException < Exception; end

def auth_info
  # This will only be defined when in App Engine production and if Cloud Endpoints is configured correctly
  encoded_info = request.env["HTTP_X_ENDPOINT_API_USERINFO"]

  if encoded_info
    info_json = Base64.decode64 encoded_info
    user_info = JSON.parse info_json

    raise AuthorizationException if user_info['id'].nil? || user_info['id'].length == 0

    return user_info
  else
    raise AuthorizationException
  end
end

post "/key" do
  content_type 'application/json'

  begin
    # Generate a random key
    pass = "<USE_A_SECURE_RANDOM_PASSWORD_HERE>"
    salt = OpenSSL::Random.random_bytes(16)
    iter = 20000
    key_len = 16

    auth = auth_info
    user_id = auth['id']

    raw_key = OpenSSL::PKCS5.pbkdf2_hmac_sha1(pass, salt, iter, key_len)

    # Request list of key rings
    encrypt_request_object = Google::Apis::CloudkmsV1::EncryptRequest.from_json({
      "plaintext": Base64.urlsafe_encode64(user_id + "|" + Base64.urlsafe_encode64(raw_key).sub(/==\n?$/, ""))
    }.to_json)
    response = kms_client.encrypt_crypto_key(key_name, encrypt_request_object)

    {
      "key": Base64.urlsafe_encode64(raw_key).sub(/==\n?$/, ""),
      "encrypted": Base64.urlsafe_encode64(response.ciphertext).sub(/==\n?$/, "")
    }.to_json

  rescue AuthorizationException => e
    status 401
    return {
      "success": false,
      "error": "Not authorised"
    }.to_json

  rescue => e

    error = nil

    begin
      error = {
        "body": e.body,
        "header": e.header,
        "status_code": e.status_code
      }
    rescue => e2
      error = e
    end

    return {
      "success": false,
      "error": error
    }.to_json
  end

  #Google::Apis::CloudkmsV1::EncryptResponse


end

get "/decrypt" do
  content_type 'application/json'

  input = params[:value]

  begin
    auth = auth_info
    user_id = auth['id']

    # Request list of key rings
    decrypt_request_object = Google::Apis::CloudkmsV1::DecryptRequest.from_json({
      "ciphertext": input
    }.to_json)
    response = kms_client.decrypt_crypto_key(key_name, decrypt_request_object)

    components = response.plaintext.split("|", 2)

    unless components.first == user_id
      $stderr.puts "Auth failure comparing user IDs #{components.first} with #{user_id}"
      raise AuthorizationException
    end

    {
      "key": components.last.sub(/==\n?$/, "")
    }.to_json

  rescue AuthorizationException => e
    status 401
    return {
      "success": false,
      "error": "Not authorised"
    }.to_json

  rescue => e
    return {
      "success": false,
      "input": input,
      "error": {
        "body": e.body,
        "header": e.header,
        "status_code": e.status_code
      }
    }.to_json
  end
end

get "/_ah/health" do
  { "success": true }.to_json
end
# [END app]

