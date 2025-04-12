import pyaudio
import wave
import datetime
import requests
from api_secrets import API_KEY_ASSEMBLYAI
import time
import pyttsx3
import pywhatkit
import datetime
import wikipedia
from wikipedia.exceptions import DisambiguationError
import pyjokes

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

def record_mic():
    p = pyaudio.PyAudio()
    filename=datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".wav"
    try:
        # Initialize the audio stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER
        )

        print("Listening...")

        seconds = 5  # Duration of the recording in seconds
        frames = []

        # Record audio
        for i in range(0, int(RATE/FRAMES_PER_BUFFER*seconds)):
            data = stream.read(FRAMES_PER_BUFFER)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

    except pyaudio.PyAudioError as e:
        print(f"Error initializing microphone stream: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error while recording: {e}")
        return None

    try:
        obj = wave.open("data/" + filename, "wb")
        obj.setnchannels(CHANNELS)
        obj.setsampwidth(p.get_sample_size(FORMAT))
        obj.setframerate(RATE)
        obj.writeframes(b"".join(frames))

        print(f"Recording saved to {filename}")
        return filename

    except IOError as e:
        print(f"Error saving the file {filename}: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error while saving the file: {e}")
        return None

    finally:
        return filename
    
# Upload
upload_endpoint = "https://api.assemblyai.com/v2/upload"
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"

headers = {'authorization': API_KEY_ASSEMBLYAI}

def upload(filename):
    def read_file(filename, chunk_size=5242880):
        with open(filename, "rb") as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data

    upload_response = requests.post(upload_endpoint,
                            headers=headers,
                            data=read_file(filename))

    # print(upload_response.json())

    audio_url = upload_response.json()['upload_url']
    return audio_url

# Transcribe
def transcribe(audio_url):
    transcribe_request = {"audio_url": audio_url}
    transcribe_response = requests.post(transcript_endpoint,
                            json=transcribe_request,
                            headers=headers)
    # print(transcribe_response.json()) 
    job_id = transcribe_response.json()['id']
    return job_id

# print(transcript_id)

# Poll
def poll(transcript_id):
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    polling_response = requests.get(polling_endpoint, headers=headers)
    # print(polling_response.json())
    return(polling_response.json())

def get_transcription_result_url(audio_url):
    transcript_id = transcribe(audio_url)
    while True:
        data = poll(transcript_id)
        if data['status'] == 'completed':
            return data, None
        elif data['status'] == 'error':
            return data, data['error']
        print('Waiting 1 seconds...')
        time.sleep(1)

# Save transcribe
def save_transcript(filename, time_str, audio_url):
    data, error = get_transcription_result_url(audio_url)

    if data:
        with open(filename, "a") as f:
            f.write(time_str)
            f.write(data['text'] + '\n')
        print(data['text'])
        print("Transription saved!!")
        return data['text']
    elif error:
        print("Error!!", error)
        return "Error"
    

engine = pyttsx3.init()

voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

def talk(text):
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    while True:
        filename = record_mic()
        print(filename)
        audio_url = upload("data/" + filename)
        time_str = filename.replace(".wav", ": ")
        command = save_transcript("recording_records.txt" , time_str, audio_url).lower()

        print(command)
        if "stop" in command:
            talk("Stopping the loop")
            with open("recording_records.txt", "a") as f:
                f.write("Bot: Stopping the loop\n")
            break

        elif "play" in command:
            song = command.replace('play', '')
            talk("Playing" + song)
            with open("recording_records.txt", "a") as f:
                f.write("Bot: Playing " + song + "\n")
            pywhatkit.playonyt(song)

        elif "time" in command:
            time = datetime.datetime.now().strftime('%I:%M %p')
            print(time)
            talk("Current time is " + time)
            with open("recording_records.txt", "a") as f:
                f.write("Bot: Current time is " + time + "\n")

        elif "find" in command:
            person = command.replace("find", "")
            try:
                info = wikipedia.summary(person, sentences=1)
                talk(info)
            except DisambiguationError as e:
                # Automatically pick the first option from the disambiguation list
                first_option = e.options[0]
                print(f"Picking the first option: {first_option}")
                info = wikipedia.summary(first_option, sentences=1)
                talk(info)
            with open("recording_records.txt", "a") as f:
                f.write("Bot: " + info + "\n")

        elif 'joke' in command:
            joke = pyjokes.get_joke()
            print(joke)
            talk(joke)
            with open("recording_records.txt", "a") as f:
                f.write("Bot: " + joke + "\n")
        
        else:
            talk("What did you say?")
            with open("recording_records.txt", "a") as f:
                f.write("Bot: What did you say?\n")