from google.cloud import storage
from datetime import date
import requests
import json
import os
import calendar
import time
import urllib.parse

api_token = os.environ['SLACK_APP_TOKEN']
bucket_name = os.environ['SLACK_BUCKET_NAME']
events_to_retrieve = 1000  # maximum of 9,999 - https://api.slack.com/admins/audit-logs-call
url = "https://api.slack.com/audit/v1/logs"
today = calendar.timegm(time.strptime(f'{date.today().year}-{date.today().month}-{date.today().day} 00:00:00', '%Y-%m-%d %H:%M:%S'))

client = storage.Client()
bucket = client.get_bucket(bucket_name)


def main(*args):
    """
    This is a fully stateless function. The pagination cursor and log events are stored in a GCS bucket.
    It shouldn't be too much effort to modify this function to utilise AWS/Azure. If you do, please submit a
    PR to the "github.com/algbra-labs-oss/chronicle" repository.

    A couple of things happen here:
    -   First we try to retrieve the pagination cursor from the storage bucket, if it exists.
        If the cursor file doesn't exist, we assign an empty string to the variable.

    -   Next, we send a request to the Slack audit log endpoint.
        If the cursor variable is empty then we send a GET request with the query parameter "oldest" so that we collect
        all logs from 00:00:00 *today*.
        If a cursor is returned, we store it. If a cursor isn't returned, we store the timestamp of last execution instead.

    -   Lastly, we write each event object to the bucket as a separate .json file
    """
    try:
        blob = bucket.get_blob('cursor')
        cursor = blob.download_as_text()
    except:
        cursor = ""

    try:
        blob = bucket.get_blob('last_execution_timestamp')
        last_execution_timestamp = blob.download_as_text()
    except:
        last_execution_timestamp = ""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    now = time.time()

    try:
        if cursor:
            print(f"INFO: Cursor exists in the bucket. Continuing.")
            response = requests.get(f"{url}?limit={events_to_retrieve}&cursor={urllib.parse.quote_plus(cursor)}", headers=headers)
            if response.status_code == requests.codes.ok:
                print(f"INFO: Status code is OK. Writing execution timestamp ({now}) to bucket.")
                blob = bucket.blob('last_execution_timestamp')
                blob.upload_from_string(str(now))

                if response.json()['response_metadata']['next_cursor']:
                    print(f"INFO: Found a cursor. Writing to bucket ({str(response.json()['response_metadata']['next_cursor'])}).")
                    blob = bucket.blob('cursor')
                    blob.upload_from_string(str(response.json()['response_metadata']['next_cursor']))
                else:
                    print(f"INFO: No cursor found. Continuing.")
                    blob = bucket.blob('cursor')
                    blob.upload_from_string("")

                if response.json()['entries']:
                    print(f"INFO: {len(response.json()['entries'])} entries found. Writing to bucket.")
                    for item in response.json()['entries']:
                        print(item)
                        blob = bucket.blob(f"logs/{item['id']}.json")
                        blob.upload_from_string(data=json.dumps(item), content_type='application/json')
                else:
                    print("INFO: No logs to process. Pretty quiet today.")
            else:
                print(f"ERROR: Problem retrieving logs. {response.status_code}, {response.text}")

        else:
            if last_execution_timestamp:
                timestamp = last_execution_timestamp
                print(f"INFO: Cursor does not exist. Using the last_execution_timestamp ({timestamp})")
            else:
                timestamp = today
                print(f"INFO: Cursor does not exist. Using timestamp from beginning-of-day ({timestamp})")

            response = requests.get(f"{url}?limit={events_to_retrieve}&oldest={timestamp}", headers=headers)
            if response.status_code == requests.codes.ok:
                print(f"INFO: Status code is OK. Writing execution timestamp ({now}) to bucket.")
                blob = bucket.blob('last_execution_timestamp')
                blob.upload_from_string(str(now))

                if response.json()['response_metadata']['next_cursor']:
                    print(f"INFO: Found a cursor. Writing to bucket.")
                    blob = bucket.blob('cursor')
                    blob.upload_from_string(str(response.json()['response_metadata']['next_cursor']))
                else:
                    print(f"INFO: No cursor found. Continuing.")
                    blob = bucket.blob('cursor')
                    blob.upload_from_string("")

                if response.json()['entries']:
                    print(f"INFO: {len(response.json()['entries'])} entries found. Writing to bucket.")
                    for item in response.json()['entries']:
                        blob = bucket.blob(f"logs/{item['id']}.json")
                        blob.upload_from_string(data=json.dumps(item), content_type='application/json')
                else:
                    print("INFO: No logs to process. Pretty quiet today.")
            else:
                print(f"ERROR: Problem retrieving logs. {response.status_code}, {response.text}")

    except Exception as error:
        print(f"ERROR: {error}")
