from daily import *
import requests
from daily_call import DailyCall

SAMPLE_RATE = 16000
CHANNELS = 1


def create_web_call(api_url, api_key, assistant):
    url = f"{api_url}/call/web"
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=assistant)
    data = response.json()
    if response.status_code == 201:
        call_id = data.get('id')
        web_call_url = data.get('webCallUrl')
        return call_id, web_call_url
    else:
        print(f"Error: {data['message']}")
        return None


class Vapi:
    def __init__(self, *, api_key, api_url="https://api.vapi.ai"):
        self.api_key = api_key
        self.api_url = api_url

    def start(self, *, assistant_id=None, assistant=None):
        # Start a new call
        if assistant_id:
            assistant = {'assistantId': assistant_id}
        elif assistant:
            assistant = {'assistant': assistant}

        call_id, web_call_url = create_web_call(
            self.api_url, self.api_key, assistant)

        print('Joining call... ' + call_id)

        if not web_call_url:
            raise Exception("Error: Unable to create call.")

        self.__client = DailyCall()
        self.__client.join(web_call_url)

    def stop(self):
        self.__client.leave()
        self.__client = None
