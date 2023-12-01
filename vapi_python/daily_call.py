import daily
import threading
import pyaudio
import time

SAMPLE_RATE = 16000
NUM_CHANNELS = 1
BYTES_PER_SAMPLE = 2


def is_playable_speaker(participant):
    is_speaker = "userName" in participant["info"] and participant["info"]["userName"] == "Vapi Speaker"
    mic = participant["media"]["microphone"]
    is_subscribed = mic["subscribed"] == "subscribed"
    is_playable = mic["state"] == "playable"
    return is_speaker and is_subscribed and is_playable


class DailyCall(daily.EventHandler):
    def __init__(self):
        self.__app_quit = False
        self.__start_event = threading.Event()
        daily.Daily.init()

        self.__audio_interface = pyaudio.PyAudio()

        self.__mic_device = daily.Daily.create_microphone_device(
            "my-mic",
            sample_rate=SAMPLE_RATE,
            channels=NUM_CHANNELS,            non_blocking=True
        )

        self.__speaker_device = daily.Daily.create_speaker_device(
            "my-speaker",
            sample_rate=SAMPLE_RATE,
            channels=NUM_CHANNELS,
            non_blocking=True
        )
        daily.Daily.select_speaker_device("my-speaker")

        self.__input_audio_stream = self.__audio_interface.open(
            format=pyaudio.paInt16,
            channels=NUM_CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            stream_callback=self.on_input_stream
        )

        self.__output_audio_stream = self.__audio_interface.open(
            format=pyaudio.paInt16,
            channels=NUM_CHANNELS,
            rate=SAMPLE_RATE,
            output=True,
            stream_callback=self.on_output_stream
        )

        self.__call_client = daily.CallClient(event_handler=self)

        self.__call_client.update_inputs({
            "camera": False,
            "microphone": {
                "isEnabled": True,
                "settings": {
                    "deviceId": "my-mic",
                    "customConstraints": {
                        "autoGainControl": {"exact": True},
                        "noiseSuppression": {"exact": True},
                        "echoCancellation": {"exact": True},
                    }
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
        self.maybe_start()
        while not self.__app_quit:
            time.sleep(0.1)

    def leave(self):
        self.__app_quit = True
        self.__receive_bot_audio_thread.join()
        self.__send_user_audio_thread.join()
        self.__call_client.leave()

    def maybe_start(self):
        if self.__app_error:
            self.__start_event.set()

        if self.__app_inputs_updated and self.__app_joined:
            self.__start_event.set()

    def on_input_stream(self, in_data, frame_count, time_info, status):
        self.__start_event.wait()
        if self.__app_quit:
            return None, pyaudio.paAbort

        # If the microphone hasn't started yet `write_frames`this will return
        # 0. In that case, we just tell PyAudio to continue.
        self.__mic_device.write_frames(in_data)

        return None, pyaudio.paContinue

    def on_output_stream(self, ignore, frame_count, time_info, status):
        self.__start_event.wait()
        if self.__app_quit:
            return None, pyaudio.paAbort

        # If the speaker hasn't started yet `read_frames` will return 0. In that
        # case, we just create silence and pass it PyAudio and tell it to
        # continue.
        buffer = self.__speaker_device.read_frames(frame_count)
        if len(buffer) == 0:
            buffer = b'\x00' * frame_count * NUM_CHANNELS * BYTES_PER_SAMPLE

        return buffer, pyaudio.paContinue
