import speech_recognition as sr
from os import path
from pydub import AudioSegment

# convert mp3 file to wav
sound = AudioSegment.from_mp3("123.mp3")
sound.export("123.wav", format="wav")


# transcribe audio file
AUDIO_FILE = "123.wav"

# use the audio file as the audio source
r = sr.Recognizer()
with sr.AudioFile(AUDIO_FILE) as source:
    audio = r.record(source)  # read the entire audio file

    print("Transcription: " + r.recognize_google(audio))
