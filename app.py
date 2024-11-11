from flask import Flask, render_template, request, jsonify
import os
from gtts import gTTS
from pydub import AudioSegment
import speech_recognition as sr
from googletrans import Translator
import time

app = Flask(__name__, static_folder="static")

# Initialize the Google Translator
translator = Translator()

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    try:
        data = request.get_json()
        text = data.get('text', '')
        if text.strip() == '':
            return jsonify({"error": "No text provided"}), 400
        
        tts = gTTS(text=text, lang='en')
        timestamp = str(int(time.time()))
        filename = f"static/output_audio_{timestamp}.mp3"
        tts.save(filename)
        
        return jsonify({"url": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    try:
        audio_file = request.files['audio']
        
        # Save audio file temporarily
        audio_path = 'static/temp_audio.mp3'
        audio_file.save(audio_path)

        # Convert audio to WAV format using pydub
        audio_wav_path = 'static/temp_audio.wav'
        audio = AudioSegment.from_mp3(audio_path)
        audio.export(audio_wav_path, format='wav')

        # Recognize speech using SpeechRecognition
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(audio_wav_path) as source:
            audio = recognizer.record(source)
        
        try:
            # Recognize speech using Google Speech API
            text = recognizer.recognize_google(audio)
            detected_lang = detect_language(text)
            
            # If the detected language is Hindi, translate to English
            if detected_lang == 'hi':
                translated_text = translator.translate(text, src='hi', dest='en').text
                response = jsonify({"text": translated_text, "lang": 'en'})
            else:
                response = jsonify({"text": text, "lang": detected_lang})
            
            return response

        except sr.UnknownValueError:
            return jsonify({"error": "Speech not understood"}), 400
        except sr.RequestError as e:
            return jsonify({"error": f"Could not request results from Google Speech Recognition service; {e}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up temporary files
        try:
            os.remove(audio_path)
            os.remove(audio_wav_path)
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")



# Function to detect language (using googletrans)
def detect_language(text):
    detected = translator.detect(text)
    return detected.lang

if __name__ == "__main__":
    app.run(debug=True)
