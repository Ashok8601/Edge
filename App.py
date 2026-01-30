from flask import Flask, request, jsonify, send_file
import asyncio, edge_tts, os, uuid
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Postman / any frontend se call karne ke liye

# Available voices
VOICES = {
    "English-US": ["en-US-GuyNeural", "en-US-JennyNeural"],
    "English-GB": ["en-GB-RyanNeural", "en-GB-SoniaNeural"],
    "Hindi": ["hi-IN-PrabhatNeural", "hi-IN-SwaraNeural"]
}

async def generate_tts(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text")
    voice = data.get("voice")

    if not text or not voice:
        return jsonify({"error": "Text and voice required!"}), 400

    output_file = f"tts_{uuid.uuid4().hex}.mp3"
    try:
        asyncio.run(generate_tts(text, voice, output_file))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"file": output_file})

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

@app.route("/voices")
def voices():
    return jsonify(VOICES)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
