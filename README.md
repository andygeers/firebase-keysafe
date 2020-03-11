## How do you encrypt a Firebase database?

I've written a blog post [here](http://www.geero.net/2017/05/how-to-encrypt-a-google-firebase-realtime-database/) and this is the backend auth service described there.

Firebase Keysafe is a super-simple back end service designed to be deployed to Google App Engine Standard Environment, to protect the encryption keys of mobile users authenticated using Google Firebase
by means of Google Cloud KMS.

First you need to initialise your environment:

    # download and install google app engine sdk, (https://cloud.google.com/appengine/docs/standard/python/download)
    # sort your path, restart your terminal

    gcloud components install app-engine-python

    virtualenv env

To configure:

  1. Make sure you edit app.yaml and replace <YOUR_APPENGINE_APP_ID_HERE> with the name of your App Engine app.
  2. In main.py, plug in values for <USE_A_SECURE_RANDOM_PASSWORD_HERE>, <KMS_KEYRING_NAME>, <KMS_KEY_ID> and <PUT_SOME_RANDOM_API_KEY_THAT_YOU_REQUIRE_HERE>

Then each time you want to test you do this:

    source env/bin/activate

    pip install -t lib -r requirements.txt

    dev_appserver.py app.yaml

    deactivate

To use:

  1. All requests need a query parameter 'key=<PUT_SOME_RANDOM_API_KEY_THAT_YOU_REQUIRE_HERE>' and an "Authorization" HTTP header of the form "Bearer <JWT>"
  2. POST to '/key' to generate yourself a new encryption key. Returns JSON with "key" (the actual encryption key / DEK) and "encrypted" (that you can store safely in Firebase)
  3. On a new device, make a GET to '/decrypt?value=<encrypted_key>' (where encrypted_key is the value you stored in Firebase in the previous step). This will return JSON with "key" being the decrypted DEK.

It also supports group encryption keys if you use [Firebase Custom Claims](https://firebase.google.com/docs/auth/admin/custom-claims) to add "groups=g1,g2,g3" to your users' JWTs. POST to '/groupkey?group=g1' to generate a group key, and
any member of that group can then use the same '/decrypt?value=<encrypted_key>' endpoint to decrypt that key.

To deploy:

    gcloud app deploy

To run unit tests:

    python runner.py "{google-cloud-sdk-path}"

## License

    Copyright (c) 2017 Andy Geers.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.


