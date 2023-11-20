from daily import *
import threading
import pyaudio
import time
import pulsectl
import subprocess

SAMPLE_RATE = 16000
NUM_CHANNELS = 1
CHUNK_SIZE = 640


class DailyCall:
    def __init__(self):
        Daily.init()

        # Create a PulseAudio client
        pulse = pulsectl.Pulse('my-client')

        # Load the echo cancellation module
        subprocess.run(['pactl', 'load-module', 'module-echo-cancel'])

        # Get the name of the echo cancelled source
        echo_cancel_source = None
        for source in pulse.source_list():
            if 'echo-cancel' in source.name:
                echo_cancel_source = source
                break
        print("-------")
        if echo_cancel_source is None:
            raise RuntimeError('Failed to find echo cancelled source')

        # Set the echo cancelled source as the default
        pulse.default_set(echo_cancel_source)

        self.__audio_interface = pyaudio.PyAudio()

        echo_cancel_source_index = None
        for i in range(self.__audio_interface.get_device_count()):
            device_info = self.__audio_interface.get_device_info_by_index(i)
            print(device_info)
            if 'echo-cancel' in device_info.get('name'):
                echo_cancel_source_index = i
                break

        if echo_cancel_source_index is None:
            raise RuntimeError('Failed to find echo cancelled source')

        self.__input_audio_stream = self.__audio_interface.open(
            format=pyaudio.paInt16,
            channels=NUM_CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            input_device_index=echo_cancel_source_index,
        )

        self.__output_audio_stream = self.__audio_interface.open(
            format=pyaudio.paInt16,
            channels=NUM_CHANNELS,
            rate=SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE
        )

        self.__mic_device = Daily.create_microphone_device(
            "my-mic",
            sample_rate=SAMPLE_RATE,
            channels=NUM_CHANNELS
        )

        self.__speaker_device = Daily.create_speaker_device(
            "my-speaker",
            sample_rate=SAMPLE_RATE,
            channels=NUM_CHANNELS
        )
        Daily.select_speaker_device("my-speaker")

        self.__client = CallClient()

        self.__client.update_inputs({
            "camera": False,
            "microphone": {
                "isEnabled": True,
                "settings": {
                    "deviceId": "my-mic"
                }
            }
        }, completion=self.on_inputs_updated)

        self.__client.update_subscription_profiles({
            "base": {
                "camera": "unsubscribed",
                "microphone": "subscribed"
            }
        })

        self.__app_quit = False
        self.__app_error = None
        self.__app_joined = False
        self.__app_inputs_updated = False

        self.__start_event = threading.Event()
        self.__send_thread = threading.Thread(target=self.send_audio)
        self.__receive_thread = threading.Thread(target=self.receive_audio)
        self.__send_thread.start()
        self.__receive_thread.start()

    def on_inputs_updated(self, inputs, error):
        if error:
            print(f"Unable to updated inputs: {error}")
            self.__app_error = error
        else:
            self.__app_inputs_updated = True
        self.maybe_start()

    def on_joined(self, data, error):
        if error:
            print(f"Unable to join meeting: {error}")
            self.__app_error = error
        else:
            self.__app_joined = True
            print("Joined meeting!")
        self.maybe_start()

    def join(self, meeting_url):
        self.__client.join(meeting_url, completion=self.on_joined)

    def leave(self):
        self.__app_quit = True
        self.__send_thread.join()
        self.__receive_thread.join()
        self.__client.leave()

    def maybe_start(self):
        if self.__app_error:
            self.__start_event.set()

        if self.__app_inputs_updated and self.__app_joined:
            self.__start_event.set()

    def send_audio(self):
        self.__start_event.wait()

        if self.__app_error:
            print(f"Unable to send audio!")
            return

        while not self.__app_quit:
            buffer = self.__input_audio_stream.read(
                CHUNK_SIZE, exception_on_overflow=False)
            if len(buffer) > 0:
                self.__mic_device.write_frames(buffer)

    def receive_audio(self):
        self.__start_event.wait()
        time.sleep(3)
        self.__client.send_app_message("playable")

        if self.__app_error:
            print(f"Unable to receive audio!")
            return

        while not self.__app_quit:
            buffer = self.__speaker_device.read_frames(CHUNK_SIZE)
            if len(buffer) > 0:
                self.__output_audio_stream.write(buffer, CHUNK_SIZE)
