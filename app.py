import os
import requests
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from dotenv import load_dotenv
import pytz

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'weather-app-secret-key')

# OpenWeatherMap API configuration
# API_KEY = os.getenv('OPENWEATHER_API_KEY')
# BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
# FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
API_KEY = "e65ecad190msh55277ef9b131cfcp1d172ajsnda09ee42d5fd"
BASE_URL = "weatherapi-com.p.rapidapi.com"
FORECAST_URL = "https://weatherapi-com.p.rapidapi.com/alerts.json"

# Weather icon mapping
WEATHER_ICONS = {
    '01d': 'clear-day',
    '01n': 'clear-night',
    '02d': 'partly-cloudy-day',
    '02n': 'partly-cloudy-night',
    '03d': 'cloudy',
    '03n': 'cloudy',
    '04d': 'cloudy',
    '04n': 'cloudy',
    '09d': 'rain',
    '09n': 'rain',
    '10d': 'rain',
    '10n': 'rain',
    '11d': 'thunderstorm',
    '11n': 'thunderstorm',
    '13d': 'snow',
    '13n': 'snow',
    '50d': 'fog',
    '50n': 'fog'
}

def get_weather_data(city, units='metric'):
    """Fetch current weather and forecast data from OpenWeatherMap API"""
    try:
        # Current weather
        current_params = {
            "q": city,
            "units": units,
            "appid": API_KEY
        }
        current_response = requests.get(BASE_URL, params=current_params)
        current_response.raise_for_status()
        current_data = current_response.json()
        
        # Forecast
        forecast_params = {
            "q": city,
            "units": units,
            "appid": API_KEY
        }
        forecast_response = requests.get(FORECAST_URL, params=forecast_params)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        return current_data, forecast_data
    
    except requests.exceptions.RequestException as e:
        return None, None

def process_weather_data(current_data, forecast_data, units):
    """Process the raw API data into a more usable format"""
    if not current_data or not forecast_data:
        return None
    
    # Process current weather
    processed_current = {
        'city': current_data['name'],
        'country': current_data['sys']['country'],
        'temp': round(current_data['main']['temp']),
        'feels_like': round(current_data['main']['feels_like']),
        'humidity': current_data['main']['humidity'],
        'pressure': current_data['main']['pressure'],
        'wind_speed': current_data['wind']['speed'],
        'wind_deg': current_data['wind'].get('deg', 0),
        'description': current_data['weather'][0]['description'].title(),
        'icon': current_data['weather'][0]['icon'],
        'icon_class': WEATHER_ICONS.get(current_data['weather'][0]['icon']),
        'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%H:%M'),
        'sunset': datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%H:%M'),
        'units': '°C' if units == 'metric' else '°F',
        'speed_units': 'm/s' if units == 'metric' else 'mph'
    }
    
    # Process forecast data
    processed_forecast = []
    for item in forecast_data['list']:
        if item['dt_txt'].endswith('12:00:00'):  # Only get midday forecasts
            forecast_day = {
                'date': datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S').strftime('%a, %b %d'),
                'temp': round(item['main']['temp']),
                'description': item['weather'][0]['description'].title(),
                'icon': item['weather'][0]['icon'],
                'icon_class': WEATHER_ICONS.get(item['weather'][0]['icon']),
                'humidity': item['main']['humidity']
            }
            processed_forecast.append(forecast_day)
    
    return {
        'current': processed_current,
        'forecast': processed_forecast
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    if request.method == 'POST':
        city = request.form.get('city')
        units = request.form.get('units', 'metric')
    else:
        city = request.args.get('city', 'London')
        units = request.args.get('units', 'metric')
    
    if not city:
        return render_template('index.html', error="Please enter a city name")
    
    current_data, forecast_data = get_weather_data(city, units)
    
    if not current_data or not forecast_data:
        return render_template('index.html', error="Could not retrieve weather data. Please check the city name and try again.")
    
    weather_data = process_weather_data(current_data, forecast_data, units)
    
    if not weather_data:
        return render_template('index.html', error="Error processing weather data")
    
    return render_template('weather.html', weather=weather_data, units=units)

@app.route('/api/weather')
def api_weather():
    city = request.args.get('city', 'London')
    units = request.args.get('units', 'metric')
    
    current_data, forecast_data = get_weather_data(city, units)
    
    if not current_data or not forecast_data:
        return jsonify({'error': 'Could not retrieve weather data'}), 404
    
    weather_data = process_weather_data(current_data, forecast_data, units)
    
    if not weather_data:
        return jsonify({'error': 'Error processing weather data'}), 500
    
    return jsonify(weather_data)

if __name__ == '__main__':
    app.run(debug=True)
