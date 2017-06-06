## How do you encrypt a Firebase database?

I've written a blog post [here](http://www.geero.net/2017/05/how-to-encrypt-a-google-firebase-realtime-database/) and this is the backend auth service described there.

Firebase Keysafe is a super-simple back end service designed to be deployed to Google App Engine Flexible Environment and Cloud Endpoints, to protect the encryption keys of mobile users authenticated using Google Firebase
by means of Google Cloud KMS.

To configure:

  1. Make sure you edit openapi.yaml and replace <YOUR_APPENGINE_APP_ID_HERE> with the name of your App Engine app, and <YOUR_FIREBASE_PROJECT_ID> with the Project ID that houses your Firebase Auth.
  2. Do the same in app.yaml
  3. Plug in values for <USE_A_SECURE_RANDOM_PASSWORD_HERE>, <KMS_KEYRING_NAME> and <KMS_KEY_ID> in app.rb
  3. Deploy the configuration to Google Cloud Endpoints:

        gcloud service-management deploy openapi.yaml

  4. You will then be given a config_id that you can plug in to app.yaml.
  5. Deploy to App Engine:

        bundle install
        gcloud app deploy

To run in development mode:

        bundle install
        bundle exec ruby app.rb -p 8080

(caveat: I couldn't actually get my local development machine to work properly with Cloud KMS - I always got permission denied errors.)



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