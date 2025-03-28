import requests
import time
import subprocess
import argparse
import json
from loguru import logger
from elv_client_py import ElvClient

from src.common import get_auth, timeit
from src.external_tag_subset import trim_tags

from config import config

def upload_external(content: str, auth: str, file: str):
    url = f"{config['tag_host']}/{content}/upload_tags?authorization={auth}"
    with open(file, "rb") as f:
        response = requests.post(url, files={"file": f})
    if response.status_code != 200:
        raise Exception(f"Error in uploading external tags: {response.text}")

def do_tagging(content: str, auth: str):
    response = requests.post(f"{config['tag_host']}/{content}/tag?authorization={auth}", json=config['tag_args'])
    if response.status_code == 200:
        logger.debug(json.dumps(response.json(), indent=2))
    else:
        raise RuntimeError(f"Error in tagging: response={response.text}\nstatus_code={response.status_code}")

    done = False
    with timeit("Awaiting tagging completion"):
        while not done:
            status = requests.get(f"{config['tag_host']}/{content}/status?authorization={auth}").json()
            for stream in status:
                for feature in status[stream]:
                    logger.debug(f"{feature} progress: {status[stream][feature]['tagging_progress']}")
            done = True
            for stream in status:
                for feature in status[stream]:
                    if status[stream][feature]['status'] != "Completed":
                        done = False
                        break
                    elif status[stream][feature]['status'] == "Failed":
                        raise RuntimeError(f"Error in tagging: {status[stream][feature]['error']}")
            time.sleep(10)

    with timeit("Finalizing"):
        response = requests.post(f"{config["tag_host"]}/{content}/finalize?leave_open=true&authorization={auth}&write_token={content}")
        if response.status_code == 200:
            logger.debug(json.dumps(response.json(), indent=2))
        else:
            raise RuntimeError(f"Error in finalizing: {response.text}")

def get_livestream_duration(content: str, client: ElvClient) -> int:
    periods = client.content_object_metadata(write_token=content, metadata_subtree="live_recording/recordings/live_offering")
    if len(periods) == 0:
        return 0
    assert len(periods) == 1
    if 'video' not in periods[0]['finalized_parts_info']:
        return 0
    num_parts = periods[0]['finalized_parts_info']['video']['n_parts']
    part_duration = 30 
    return max(0, (num_parts - 1) * part_duration)

def main():
    auth = get_auth(args.config, args.livestream)
    client = ElvClient.from_configuration_url(config['fabric_url'], auth)

    end_time = 0
    while True:
        duration = get_livestream_duration(args.livestream, client)
        if duration > end_time and duration >= config['tag_interval']:
            end_time = duration
            with timeit("Uploading external tags"):
                trim_tags(config['external_tags'].split('.')[0] + "_master.json", config['external_tags'], end_time * 1000)
                upload_external(args.livestream, auth, "rugbyviz.json")
            with timeit("Tagging"):
                do_tagging(args.livestream, auth)
            time.sleep(config["tag_interval"])
        else:
            logger.info("Livestream has not progressed enough, waiting to tag.")
            time.sleep(45)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    parser.add_argument("--livestream", type=str)
    args = parser.parse_args()
    main()