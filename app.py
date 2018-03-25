# -*- coding:utf8 -*-
# !/usr/bin/env python
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
#from future.standard_library import install_aliases
#install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    if req.get("result").get("action") != "weatherbitUV":
        return {}

    # Get city info from DialogFlow
    city_state = makeQuery(req)
    if city_state is None:
        return {}

    # API query
    API_KEY = "72c9bdba3d66475aa1a13f794d90e769"
    current_url = "https://api.weatherbit.io/v2.0/current?city=%s&key=%s"%(city_state,API_KEY)
    result = urlopen(current_url).read()
    c = json.loads(result)
    current_city = c['data'][0]['city_name']
    current_state = c['data'][0]['state_code']
    current_uv = c['data'][0]['uv']

    # Risk levels
    if current_uv <= 2.9:
        risk = "Low"
    elif current_uv <= 5.9:
        risk = "Moderate"
    elif current_uv <= 7.9:
        risk = "High"
    elif current_uv <= 10.9:
        risk = "Very high"
    else:
        risk = "Extreme"

    speech = "Current UV index in %s, %s is %.1f. The risk of harm from unprotected sun exposure is %s. "\
                %(current_city,current_state,current_uv,risk)
    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "weatherbit-uv-webhook-sample"
    }


def makeQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    state = parameters.get("geo-state-us")
    if city is None:
        return None

    city = city.replace(' ','+')
    state = state.replace(' ','+')
    city_state = city + ',' + state
    return city_state


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
