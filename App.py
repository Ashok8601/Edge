from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import asyncio
import edge_tts
import os
import uuid

app = Flask(__name__)
CORS(app)

# ===============================
# CHARACTER → VOICE MAP
# ===============================

CHARACTER_VOICES = {
    "RAVI": "en-US-GuyNeural",
    "PRIYA": "en-US-JennyNeural",
    "NARRATOR": "en-GB-RyanNeural",
    "HINDI_BOY": "hi-IN-PrabhatNeural",
    "HINDI_GIRL": "hi-IN-SwaraNeural"
}

# ===============================
# ASYNC TTS GENERATOR
# ===============================

async def generate_tts(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

# ===============================
# SCRIPT PARSER
# ===============================

def parse_script(script):
    lines = script.strip().split("\n")
    dialogues = []

    for line in lines:
        if ":" in line:
            character, text = line.split(":", 1)
            character = character.strip().upper()
            text = text.strip()

            voice = CHARACTER_VOICES.get(character)

            if voice:
                dialogues.append({
                    "voice": voice,
                    "text": text
                })

    return dialogues

# ===============================
# MERGE AUDIO USING FFMPEG
# ===============================

def merge_audio_files(audio_files, output_file):
    filelist_path = "filelist.txt"

    with open(filelist_path, "w") as f:
        for file in audio_files:
            f.write(f"file '{os.path.abspath(file)}'\n")

    os.system(f"ffmpeg -f concat -safe 0 -i {filelist_path} -c copy {output_file}")

    os.remove(filelist_path)

# ===============================
# AUDIOBOOK ENDPOINT
# ===============================

@app.route("/audiobook", methods=["POST"])
def audiobook():
    data = request.get_json()
    script = data.get("script")

    if not script:
        return jsonify({"error": "Script is required"}), 400

    dialogues = parse_script(script)

    if not dialogues:
        return jsonify({"error": "No valid character lines found"}), 400

    session_id = uuid.uuid4().hex
    final_file = f"audiobook_{session_id}.mp3"

    try:
        async def generate_full():
            with open(final_file, "wb") as f:
                for dialogue in dialogues:
                    communicate = edge_tts.Communicate(
                        dialogue["text"],
                        dialogue["voice"]
                    )
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])

        asyncio.run(generate_full())

        # IMPORTANT: Check file exists
        if not os.path.exists(final_file):
            return jsonify({"error": "File generation failed"}), 500

        return jsonify({
            "message": "Audiobook generated successfully",
            "file": final_file,
            "download_url": f"/download/{final_file}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ===============================
# DOWNLOAD ENDPOINT
# ===============================

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(os.getcwd(), filename)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)

    return jsonify({"error": "File not found"}), 404

# ===============================
# CHARACTER LIST ENDPOINT
# ===============================

@app.route("/characters")
def characters():
    return jsonify(CHARACTER_VOICES)

# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
