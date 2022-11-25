from google.cloud import storage
from datetime import date
import requests
import json
import os

api_token = os.environ['EVENTS_API_TOKEN']
bucket_name = os.environ['BUCKET_NAME']
events_to_retrieve = 100
url = "https://events.1password.com"  # https://developer.1password.com/docs/events-api/reference/#servers
client = storage.Client()
bucket = client.get_bucket(bucket_name)


def main(*args):
    """
    This is a fully stateless function. The pagination cursor and log events are stored in a GCS bucket.
    It shouldn't be too much effort to modify this function to utilise AWS/Azure. If you do, please submit a
    PR to the "github.com/algbra-labs-oss/chronicle" repository.

    A couple of things happen here:
    -   First we try to retrieve the pagination cursor from the storage bucket, if it exists.
        If the cursor file doesn't exist, we assign a null value to the cursor variable.

    -   Next, we send a request to the appropriate 1Password endpoints.
        If the cursor variable is None then we send a "reset cursor" object which grabs the first `n` events
        from 00:00:00 *today*. A cursor object will be stored and the function will continue retrieving the next `n`
        events the next time it runs.
        If there is a cursor, we send it as part of the POST to the 1Password API to query for the next set of objects

    -   If we get a successful response status code, we store the cursor to the storage bucket

    -   Lastly, we write each event object to the bucket as a separate .json file

    """
    try:
        blob = bucket.get_blob('signinattempts/metadata')
        signinattempts_cursor = blob.download_as_text()
    except:
        signinattempts_cursor = None

    try:
        blob = bucket.get_blob('itemusages/metadata')
        itemusages_cursor = blob.download_as_text()
    except:
        itemusages_cursor = None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    reset_cursor_object = {
        "limit": events_to_retrieve,
        "start_time": f"{date.today()}T00:00:00-00:00",
    }

    signinattempts_cursor_object = {
        "cursor": f"{signinattempts_cursor}",
    }

    itemusages_cursor_object = {
        "cursor": f"{itemusages_cursor}",
    }

    try:
        if signinattempts_cursor:
            response = requests.post(f"{url}/api/v1/signinattempts", headers=headers, json=signinattempts_cursor_object)
            if response.status_code == requests.codes.ok:
                blob = bucket.blob('signinattempts/metadata')
                blob.upload_from_string(str(response.json()['cursor']))
                if response.json()['items']:
                    for item in response.json()['items']:
                        blob = bucket.blob(f"signinattempts/{item['uuid']}.json")
                        blob.upload_from_string(data=json.dumps(item), content_type='application/json')
                else:
                    print("INFO: No /signinattempts logs to process. Pretty quiet today.")
            else:
                print(f"ERROR: Problem retrieving /signinattempts logs. {response.status_code}, {response.text}")

        else:
            response = requests.post(f"{url}/api/v1/signinattempts", headers=headers, json=reset_cursor_object)
            if response.status_code == requests.codes.ok:
                blob = bucket.blob('signinattempts/metadata')
                blob.upload_from_string(str(response.json()['cursor']))
                if response.json()['items']:
                    for item in response.json()['items']:
                        blob = bucket.blob(f"signinattempts/{item['uuid']}.json")
                        blob.upload_from_string(data=json.dumps(item), content_type='application/json')
                else:
                    print("INFO: No /signinattempts logs to process. Pretty quiet today.")
            else:
                print(f"ERROR: Problem retrieving /signinattempts logs. {response.status_code}, {response.text}")

    except Exception as error:
        print(f"ERROR: {error}")

    try:
        if itemusages_cursor:
            response = requests.post(f"{url}/api/v1/itemusages", headers=headers, json=itemusages_cursor_object)
            if response.status_code == requests.codes.ok:
                blob = bucket.blob('itemusages/metadata')
                blob.upload_from_string(str(response.json()['cursor']))
                if response.json()['items']:
                    for item in response.json()['items']:
                        blob = bucket.blob(f"itemusages/{item['uuid']}.json")
                        blob.upload_from_string(data=json.dumps(item), content_type='application/json')
                else:
                    print("INFO: No /itemusages logs to process. Pretty quiet today.")
            else:
                print(f"ERROR: Problem retrieving /itemusages logs. {response.status_code}, {response.text}")

        else:
            response = requests.post(f"{url}/api/v1/itemusages", headers=headers, json=reset_cursor_object)
            if response.status_code == requests.codes.ok:
                blob = bucket.blob('itemusages/metadata')
                blob.upload_from_string(str(response.json()['cursor']))
                if response.json()['items']:
                    for item in response.json()['items']:
                        blob = bucket.blob(f"itemusages/{item['uuid']}.json")
                        blob.upload_from_string(data=json.dumps(item), content_type='application/json')
                else:
                    print("INFO: No /itemusages logs to process. Pretty quiet today.")
            else:
                print(f"ERROR: Problem retrieving /itemusages logs. {response.status_code}, {response.text}")

    except Exception as error:
        print(f"ERROR: {error}")
