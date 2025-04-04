import requests
import time
import argparse
import json
from loguru import logger
from elv_client_py import ElvClient

from src.common import get_auth, timeit, get_livestream_duration, get_num_periods, get_livestream_token
from src.external_tag_subset import trim_tags

from config import config

def upload_external(content: str, auth: str, file: str):
    url = f"{config['tag_host']}/{content}/upload_tags?authorization={auth}"
    with open(file, "rb") as f:
        response = requests.post(url, files={"file": f})
    if response.status_code != 200:
        logger.error(f"Error in uploading external tags: {response.text}. Continuing anyway, but something is wrong.")

def do_tagging(content: str, auth: str):
    # submit tag request
    response = requests.post(f"{config['tag_host']}/{content}/tag?authorization={auth}", json=config['tag_args'])
    if response.status_code == 200:
        logger.debug(json.dumps(response.json(), indent=2))
    else:
        raise RuntimeError(f"Error in tagging: response={response.text}\nstatus_code={response.status_code}")

    done = False
    with timeit("Awaiting tagging completion"):
        while not done:
            status = requests.get(f"{config['tag_host']}/{content}/status?authorization={auth}").json()
            progress = {}
            for stream in status:
                for feature in status[stream]:
                    progress[feature] = status[stream][feature]['tagging_progress'] or "fetching parts"
            logger.info(progress)
            done = True
            for stream in status:
                for feature in status[stream]:
                    if status[stream][feature]['status'] == "Failed":
                        raise RuntimeError(f"Error in tagging: {status[stream][feature]['error']}")
                    if status[stream][feature]['status'] != "Completed":
                        done = False
                        break
            time.sleep(10)

    with timeit("Finalizing"):
        response = requests.post(f"{config['tag_host']}/{content}/finalize?leave_open=true&authorization={auth}&write_token={content}")
        if response.status_code == 200:
            logger.debug(json.dumps(response.json(), indent=2))
        else:
            logger.error("There was an error finalizing, continuing to run tagger.")

def main():
    auth = get_auth(args.config, args.livestream)
    client = ElvClient.from_configuration_url(config['fabric_url'], auth)

    end_time = 0
    last_token = None
    while True:
        live_token = get_livestream_token(args.livestream, client)
        if live_token == "":
            logger.info("Livestream hasn't begun, waiting")
            time.sleep(60)
            continue
        if live_token != last_token:
            logger.info("Found new stream token.")
            if last_token is not None:
                logger.info("Restarting tagging on new livestream")
            last_token = live_token
            end_time = 0
        if get_num_periods(live_token, client) > 1:
            logger.info("Found multiple periods, waiting for livestream to restart with new write token to resume tagging")
            time.sleep(300)
            continue
        duration = get_livestream_duration(live_token, client)
        if duration >= end_time + config['min_tag']:
            end_time = duration
            with timeit("Trimming external tags and uploading."):
                trim_tags(config['external_tags'].split('.')[0] + "_master.json", config['external_tags'], end_time * 1000)
                upload_external(live_token, auth, config['external_tags'])
            with timeit("Tagging"):
                do_tagging(live_token, auth)
        else:
            wait_time = max(0, end_time + config['min_tag'] - duration)
            logger.info(f"Livestream has not progressed enough, waiting {wait_time} seconds to resume tag.")
            time.sleep(wait_time)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    parser.add_argument("--livestream", type=str)
    args = parser.parse_args()
    main()