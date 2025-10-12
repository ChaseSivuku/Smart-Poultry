from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO
from random import randint, uniform
import threading, time, random
import google.generativeai as genai
from collections import deque
from datetime import datetime, timedelta
import os
from google.cloud import texttospeech

# --- Flask Setup ---
app = Flask(__name__, static_folder="build", static_url_path="")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# --- Gemini AI Setup ---
GEMINI_API_KEY = "AIzaSyCinvKHFMi5nhOqLbgwsKi11TuCdan5rKs"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro-latest')

# --- Global Sensor Data ---
current_data = {
    "temperature": 27.5,
    "humidity": 60.0,
    "tankLevel": 80,
    "feed": 65,
    "light": 400
}

# google-cloud-texttospeech minimum version 2.29.0 is required.



PROJECT_ID = ""

def synthesize(prompt: str, text: str, output_filepath: str = "output.mp3"):
    """Synthesizes speech from the input text and saves it to an MP3 file.

    Args:
        prompt: Styling instructions on how to synthesize the content in
          the text field.
        text: The text to synthesize.
        output_filepath: The path to save the generated audio file.
          Defaults to "output.mp3".
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)

    # Select the voice you want to use.
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="Charon",  # Example voice, adjust as needed
        model_name="gemini-2.5-pro-tts"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type.
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(output_filepath, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio content written to file: {output_filepath}")

# --- Data History Storage ---
data_history = deque(maxlen=300)  # Store last 5 minutes of data (300 entries at 1-second intervals)
activity_history = deque(maxlen=50)  # Store last 50 activity events
hotspot_history = deque(maxlen=100)  # Store last 100 hotspot scans

def add_to_history():
    """Add current sensor data to history"""
    timestamp = datetime.now()
    data_entry = {
        "timestamp": timestamp.isoformat(),
        "temperature": current_data["temperature"],
        "humidity": current_data["humidity"],
        "tankLevel": current_data["tankLevel"],
        "feed": current_data["feed"],
        "light": current_data["light"]
    }
    data_history.append(data_entry)

@app.route('/api/sensor-data')
def get_sensor_data():
    add_to_history()  # Add current data to history
    return jsonify(current_data)

@app.route('/update-sensor', methods=['POST'])
def update_sensor_data():
    global current_data
    data = request.get_json()
    if data:
        current_data.update(data)
        socketio.emit("sensor_update", current_data)
    return jsonify({"status": "ok"})

@app.route('/activity-event', methods=['POST'])
def activity_event():
    """Handles automation and manual activity events (one-time notifications)."""
    data = request.get_json()
    print("Activity Event Request Received:", data)

    if not data:
        return jsonify({"error": "No data provided"}), 400

    event = {
        "title": data.get("title", "Event"),
        "detail": data.get("detail", ""),
        "color": data.get("color", "blue"),
        "time": time.strftime("%H:%M:%S"),
        "timestamp": datetime.now().isoformat()
    }

    # Store activity in history
    activity_history.append(event)

    # Broadcast the event to connected dashboard clients
    socketio.emit("activity_event", event)
    print("Activity Event Broadcast:", event)

    return jsonify({"status": "sent"})

@app.route('/system-state', methods=['POST'])
def system_state():
    """Handles system state updates from the simulation."""
    data = request.get_json()
    if data:
        # Broadcast system state to connected dashboard clients
        socketio.emit("system_state", data)
        print("System State Update:", data)
    return jsonify({"status": "ok"})

@app.route('/api/voice', methods=['POST'])
def api_voice():
    """Handles voice synthesis requests."""
    print("Voice Synthesis Request Received")
    data = request.get_json()
    prompt = data.get("prompt", "")
    text = data.get("text", "")
    output_filepath = data.get("output_filepath", "output.mp3")

    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    print(f"Synthesizing voice with prompt: {prompt}, text: {text}, output: {output_filepath}")

    synthesize(prompt, text, output_filepath)
    return jsonify({"status": "ok", "output_filepath": output_filepath})

@app.route('/hotspot-data', methods=['POST'])
def hotspot_data():
    """Handles hotspot data from the radar system."""
    data = request.get_json()
    print("Hotspot Data Received:", data)
    
    if data and 'hotspots' in data:
        # Store hotspot data in history
        timestamp = datetime.now()
        hotspot_entry = {
            "timestamp": timestamp.isoformat(),
            "hotspots": data['hotspots']
        }
        hotspot_history.append(hotspot_entry)
        
        # Broadcast hotspot data to connected dashboard clients
        socketio.emit("hotspot_data", data)
        print("Hotspot Data Broadcast:", data)
    
    return jsonify({"status": "ok"})

@app.route('/api/assistant', methods=['POST'])
def assistant_chat():
    """Handle chat requests with Gemini AI using simulation data context."""
    try:
        data = request.get_json()
        user_question = data.get('question', '')
        
        if not user_question:
            return jsonify({"error": "No question provided"}), 400

        # Prepare context from last 5 minutes of data
        recent_data = list(data_history)[-60:]  # Last 60 entries (1 minute)
        recent_activities = list(activity_history)[-10:]  # Last 10 activities
        recent_hotspots = list(hotspot_history)[-5:]  # Last 5 hotspot scans
        
        # Create context for Gemini
        context = f"""
You are an AI assistant for a Smart Chicken Farm monitoring system. Here's the recent data from the last 5 minutes:

CURRENT SENSOR READINGS:
- Temperature: {current_data['temperature']}°C
- Humidity: {current_data['humidity']}%
- Water Tank Level: {current_data['tankLevel']}%
- Feed Level: {current_data['feed']}%
- Light Intensity: {current_data['light']} lux

RECENT ACTIVITY EVENTS:
"""
        
        for activity in recent_activities:
            context += f"- {activity['title']}: {activity['detail']} at {activity['time']}\n"
        
        context += f"""
RECENT SENSOR DATA TRENDS (last minute):
"""
        
        for entry in recent_data[-10:]:  # Last 10 entries
            context += f"- {entry['timestamp'][:19]}: Temp={entry['temperature']:.1f}°C, Water={entry['tankLevel']:.1f}%, Feed={entry['feed']:.1f}%, Light={entry['light']:.1f} lux\n"

        context += f"""
CHICKEN HOTSPOT ANALYSIS (Radar Data):
"""
        
        if recent_hotspots:
            latest_hotspots = recent_hotspots[-1]['hotspots']
            context += f"Current hotspots detected: {len(latest_hotspots)}\n"
            for hotspot in latest_hotspots:
                context += f"- {hotspot['name']}: {hotspot['intensity']:.1f}% activity at ({hotspot['x']:.1f}%, {hotspot['y']:.1f}%)\n"
        else:
            context += "No recent hotspot data available.\n"

        context += f"""
Based on this comprehensive data including sensor readings, activity events, and chicken behavior hotspots, please answer the user's question: "{user_question}"

Provide helpful insights about the farm's condition, chicken behavior patterns, suggest optimizations, or explain what the data means. Consider both environmental factors and chicken movement patterns. Be concise but informative.
"""

        # Generate response using Gemini
        response = model.generate_content(context)
        
        return jsonify({
            "answer": response.text,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in assistant chat: {e}")
        return jsonify({"error": "Failed to generate response"}), 500

@app.route('/')
def serve_react():
    return send_from_directory(app.static_folder, 'index.html')





if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
