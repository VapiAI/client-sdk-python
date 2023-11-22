import daily
import threading
import pyaudio
import wave
from speexdsp import EchoCanceller

SAMPLE_RATE = 16000
NUM_CHANNELS = 1
CHUNK_SIZE = 640


def is_playable_speaker(participant):
    is_speaker = "userName" in participant["info"] and participant["info"]["userName"] == "Vapi Speaker"
    mic = participant["media"]["microphone"]
    is_subscribed = mic["subscribed"] == "subscribed"
    is_playable = mic["state"] == "playable"
    return is_speaker and is_subscribed and is_playable


class EchoCancellerWrapper():
    def __init__(self, chunk_size, filter_length, sample_rate, audio_interface):
        self.__audio_interface = audio_interface
        self.__echo_canceller = EchoCanceller.create(
            int(chunk_size / 2), filter_length, sample_rate)
        self.__mic_buffer = b''
        self.__speaker_buffer = b''

        # Initialize wav files for mic input, speaker input, and processed output
        self.__mic_wav = wave.open('mic_input.wav', 'wb')
        self.__mic_wav.setnchannels(NUM_CHANNELS)
        self.__mic_wav.setsampwidth(
            self.__audio_interface.get_sample_size(pyaudio.paInt16))
        self.__mic_wav.setframerate(SAMPLE_RATE)

        self.__speaker_wav = wave.open('speaker_input.wav', 'wb')
        self.__speaker_wav.setnchannels(NUM_CHANNELS)
        self.__speaker_wav.setsampwidth(
            self.__audio_interface.get_sample_size(pyaudio.paInt16))
        self.__speaker_wav.setframerate(SAMPLE_RATE)

        self.__output_wav = wave.open('processed_output.wav', 'wb')
        self.__output_wav.setnchannels(NUM_CHANNELS)
        self.__output_wav.setsampwidth(
            self.__audio_interface.get_sample_size(pyaudio.paInt16))
        self.__output_wav.setframerate(SAMPLE_RATE)

    def send_mic_audio(self, audio):
        self.__mic_buffer += audio

    def send_speaker_audio(self, audio):
        self.__speaker_buffer += audio

    def read(self, length):
        min_length = min(len(self.__mic_buffer), length)
        if min_length > 0:
            mic_audio = self.__mic_buffer[:min_length]
            speaker_audio = self.__speaker_buffer[:min_length]
            # If speaker buffer is less than mic buffer, pad it with silence
            if len(speaker_audio) < len(mic_audio):
                speaker_audio += b'\x00' * \
                    (len(mic_audio) - len(speaker_audio))

            self.__mic_wav.writeframes(mic_audio)
            self.__speaker_wav.writeframes(speaker_audio)

            self.__mic_buffer = self.__mic_buffer[min_length:]
            self.__speaker_buffer = self.__speaker_buffer[min_length:]
            processed_audio = self.__echo_canceller.process(
                mic_audio, speaker_audio)
            # Write processed output to wav file
            self.__output_wav.writeframes(processed_audio)
            return processed_audio
        return b''

    def __del__(self):
        # Close wav files when the object is destroyed
        self.__mic_wav.close()
        self.__speaker_wav.close()
        self.__output_wav.close()


class DailyCall(daily.EventHandler):
    def __init__(self):
        daily.Daily.init()

        self.__audio_interface = pyaudio.PyAudio()
        self.__echo_canceller = EchoCancellerWrapper(
            CHUNK_SIZE, 256, SAMPLE_RATE, self.__audio_interface)

        self.__input_audio_stream = self.__audio_interface.open(
            format=pyaudio.paInt16,
            channels=NUM_CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        self.__output_audio_stream = self.__audio_interface.open(
            format=pyaudio.paInt16,
            channels=NUM_CHANNELS,
            rate=SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE
        )

        self.__mic_device = daily.Daily.create_microphone_device(
            "my-mic",
            sample_rate=SAMPLE_RATE,
            channels=NUM_CHANNELS
        )

        self.__speaker_device = daily.Daily.create_speaker_device(
            "my-speaker",
            sample_rate=SAMPLE_RATE,
            channels=NUM_CHANNELS
        )
        daily.Daily.select_speaker_device("my-speaker")

        self.__call_client = daily.CallClient(event_handler=self)

        self.__call_client.update_inputs({
            "camera": False,
            "microphone": {
                "isEnabled": True,
                "settings": {
                    "deviceId": "my-mic"
                }
            }
        })

        self.__call_client.update_subscription_profiles({
            "base": {
                "camera": "unsubscribed",
                "microphone": "subscribed"
            }
        })

        self.__participants = dict(self.__call_client.participants())
        del self.__participants["local"]

        self.__app_quit = False
        self.__app_error = None
        self.__app_joined = False
        self.__app_inputs_updated = False

        self.__start_event = threading.Event()
        self.__receive_bot_audio_thread = threading.Thread(
            target=self.receive_bot_audio)
        self.__receive_mic_audio_thread = threading.Thread(
            target=self.receive_mic_audio)
        self.__send_echo_cancelled_mic_audio_thread = threading.Thread(
            target=self.send_echo_cancelled_mic_audio)

        self.__receive_bot_audio_thread.start()
        self.__receive_mic_audio_thread.start()
        self.__send_echo_cancelled_mic_audio_thread.start()

    def on_inputs_updated(self, inputs):
        self.__app_inputs_updated = True
        self.maybe_start()

    def on_joined(self, data, error):
        if error:
            print(f"Unable to join call: {error}")
            self.__app_error = error
        else:
            self.__app_joined = True
            print("Joined call!")
        self.maybe_start()

    def on_participant_joined(self, participant):
        self.__participants[participant["id"]] = participant

    def on_participant_left(self, participant, _):
        del self.__participants[participant["id"]]
        self.leave()

    def on_participant_updated(self, participant):
        self.__participants[participant["id"]] = participant
        if is_playable_speaker(participant):
            self.__call_client.send_app_message("playable")

    def join(self, meeting_url):
        self.__call_client.join(meeting_url, completion=self.on_joined)

    def leave(self):
        self.__app_quit = True
        self.__receive_bot_audio_thread.join()
        self.__receive_mic_audio_thread.join()
        self.__send_echo_cancelled_mic_audio_thread.join()
        self.__call_client.leave()

    def maybe_start(self):
        if self.__app_error:
            self.__start_event.set()

        if self.__app_inputs_updated and self.__app_joined:
            self.__start_event.set()

    def send_echo_cancelled_mic_audio(self):
        self.__start_event.wait()

        if self.__app_error:
            print(f"Unable to send mic audio!")
            return

        while not self.__app_quit:
            buffer = self.__echo_canceller.read(CHUNK_SIZE)
            if len(buffer) > 0:
                try:
                    self.__mic_device.write_frames(buffer)
                except Exception as e:
                    print(e)

    def receive_mic_audio(self):
        self.__start_event.wait()

        if self.__app_error:
            print(f"Unable to receive mic audio!")
            return

        while not self.__app_quit:
            buffer = self.__input_audio_stream.read(
                CHUNK_SIZE, exception_on_overflow=False)
            self.__echo_canceller.send_mic_audio(buffer)

    def receive_bot_audio(self):
        self.__start_event.wait()

        if self.__app_error:
            print(f"Unable to receive bot audio!")
            return

        while not self.__app_quit:
            buffer = self.__speaker_device.read_frames(CHUNK_SIZE)
            self.__echo_canceller.send_speaker_audio(buffer)

            if len(buffer) > 0:
                self.__output_audio_stream.write(buffer, CHUNK_SIZE)
