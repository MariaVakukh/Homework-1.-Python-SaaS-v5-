import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

API_TOKEN = ""
RSA_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def generate_weather(location, date):
    url_base_url = "https://weather.visualcrossing.com"

    url = f"{url_base_url}/VisualCrossingWebServices/rest/services/timeline/{location}/{date}?unitGroup=metric&include=days&key={RSA_KEY}&contentType=json"

    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>KMA L2: python Saas.</h2></p>"


@app.route("/weather", methods=["POST"])
def weather_endpoint():
    
    json_data = request.get_json()

    token = json_data.get("token")

    if token is None:
        raise InvalidUsage("token is required", status_code=400)
    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    timestamp = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    requester_name = json_data.get("requester_name")
    location = json_data.get("location")
    date = json_data.get("date")
    
    if requester_name is None:
        raise InvalidUsage("name is required", status_code=400)
    if location is None:
        raise InvalidUsage("location is required", status_code=400)
    if date is None:
        raise InvalidUsage("date is required", status_code=400)

    weather_data = generate_weather(location, date)['days'][0]
    
    recommendations = []
    if weather_data['temp'] < 5:
        recommendations.append("- it's easier to breathe without a runny nose, wear a hat and coat")
    if weather_data["visibility"] < 1:
        recommendations.append("- dont take your glasses, you won't see much... dense fog is expected")
    if weather_data['preciptype'] is not None:
        if "rain" in weather_data['preciptype']:
            recommendations.append("- take an umbrella, because your hair will be ruined) rain is expected")
        if "snow" in weather_data['preciptype']:
            recommendations.append("- it looks like it will snow, make yourself some delicious cocoa")
    
    
    result = {
        "requester_name": requester_name,
        "timestamp": timestamp,
        "location": location,
        "date": date,
        "weather": {
            "temp_c": f"{weather_data['temp']}",
            "feelslike_temp_c": f"{weather_data['feelslike']}",
            "wind_kph": f"{weather_data['windspeed']}",
            "pressure_mb": f"{weather_data['pressure']}",
            "humidity": f"{weather_data['humidity']}",
            "visibility_km" : f"{weather_data['visibility']}",
        },
        "x> recommendations <x": recommendations if recommendations else ["It's all in your hands."]
    }  
    
    return result


