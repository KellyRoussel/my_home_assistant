import json
import os
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'  # https://github.com/VannTen/oauth2token/issues/5

from requests_oauthlib import OAuth2Session
tenant_id="edbf5998-9a53-455a-af5a-bfd5bee80be2"
client_id="b4541a30-359d-45bf-b9a8-e88d338c60f1"
client_secret="bx98Q~W2y0l0wcrcxdAPuhtvg8_hCn4pUtXgTaix"


_base_api_url = 'https://graph.microsoft.com/v1.0/me/todo/'

oa_sess = OAuth2Session(client_id,
                        scope='openid offline_access Tasks.ReadWrite',
                        redirect_uri='https://localhost/login/authorized')

authorize_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
authorization_url, _ = oa_sess.authorization_url(authorize_url)
print(authorization_url)
redirect_resp=input("Paste redirect URL\n")

token = oa_sess.fetch_token('https://login.microsoftonline.com/common/oauth2/v2.0/token', client_secret=client_secret, authorization_response=redirect_resp)

# save token as json file
with open('secret_token.json', 'w') as f:
    json.dump(token, f, indent=4)