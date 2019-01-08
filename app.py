#!/usr/bin/env python

import urllib
import json
import os

from flask import Flask, render_template, flash, request
from flask import request
from flask import make_response
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField

# Flask app should start in global layout
app = Flask(__name__)

@app.route("/")
def hello():
    print("Hello I am here")
    return "Hello World!"
from flask import Flask
 
class ReusableForm(Form):
      name = TextField('Name:', validators=[validators.required()])
 
@app.route("/form", methods=['GET', 'POST'])
def hello1():
    form = ReusableForm(request.form)
    print form.errors
    if request.method == 'POST':
       name=request.form['name']
       print name
 
    if form.validate():
# Save the comment here.
       flash('Hello ' + name)
    else:
       flash('All the form fields are required. ')
 
return render_template('hello.html', form=form)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print("I am here")
    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)
#     res = 'assjha'
    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    print('1')
    if req.get("result").get("action") != "yahooWeatherForecast":
        return {}
    print('2')
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    print('3')
    yql_query = makeYqlQuery(req)
    print('4')
    if yql_query is None:
        print('yql query is none')
        return {}
    print('5',yql_query)
    yql_url = baseurl + urllib.urlencode({'q': yql_query}) + "&format=json"
    print('6')
    print(yql_url)
#     urllib.request.urlopen()
    result = urllib.urlopen(yql_url).read()
    print("yql result: ")
    print(result)

    data = json.loads(result)
    res = makeWebhookResult(data)
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    slack_message = {
        "text": speech,
        "attachments": [
            {
                "title": channel.get('title'),
                "title_link": channel.get('link'),
                "color": "#36a64f",

                "fields": [
                    {
                        "title": "Condition",
                        "value": "Temp " + condition.get('temp') +
                                 " " + units.get('temperature'),
                        "short": "false"
                    },
                    {
                        "title": "Wind",
                        "value": "Speed: " + channel.get('wind').get('speed') +
                                 ", direction: " + channel.get('wind').get('direction'),
                        "short": "true"
                    },
                    {
                        "title": "Atmosphere",
                        "value": "Humidity " + channel.get('atmosphere').get('humidity') +
                                 " pressure " + channel.get('atmosphere').get('pressure'),
                        "short": "true"
                    }
                ],

                "thumb_url": "http://l.yimg.com/a/i/us/we/52/" + condition.get('code') + ".gif"
            }
        ]
    }

    facebook_message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "title": channel.get('title'),
                        "image_url": "http://l.yimg.com/a/i/us/we/52/" + condition.get('code') + ".gif",
                        "subtitle": speech,
                        "buttons": [
                            {
                                "type": "web_url",
                                "url": channel.get('link'),
                                "title": "View Details"
                            }
                        ]
                    }
                ]
            }
        }
    }

    print(json.dumps(slack_message))

    return {
        "speech": speech,
        "displayText": speech,
        "data": {"slack": slack_message, "facebook": facebook_message},
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
