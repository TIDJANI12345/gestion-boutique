import sys
path = '/home/gbserver/boutique_licences'
if path not in sys.path:
    sys.path.append(path)

import os
os.environ['PA_API_SECRET'] = 'f7dc1a64e7df3a9602d8c82dcc1c0229d58b486b3e0b85fef846a63403865255'
os.environ['PA_ADMIN_PASSWORD'] = 'password'                                                                                                          
os.environ['PA_FLASK_SECRET'] = '6d3ca7a17da6078039c51ec90acc944819497b2087951f7d2154c2324d2731a4'
from api_pythonanywhere import app as application
