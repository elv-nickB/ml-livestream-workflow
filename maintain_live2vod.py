import argparse
import time
import subprocess
from loguru import logger

from elv_client_py import ElvClient

from src.common import timeit, get_auth, get_livestream_duration, get_num_periods, get_livestream_token

from config import config

INTERVAL = 5 * 60

def make_vod(livestream: str, vod: str):
    cmd = f"./elv-live-js/elv-stream copy_as_vod {livestream}  --object {vod}  --url {config['live2vod_host']}"
    subprocess.run(cmd.split())

def main():
    auth = get_auth(args.config, args.livestream)
    client = ElvClient.from_configuration_url(config["fabric_url"], static_token=auth)
    last_stream_token = None
    end_time = 0
    while True:
        stream_token = get_livestream_token(args.livestream, client)
        if stream_token == "":
            logger.info("No livestream running, waiting.")
            time.sleep(INTERVAL)
            continue
        if stream_token != last_stream_token:
            logger.info("Found new stream token")
            last_stream_token = stream_token
            end_time = 0
        if get_num_periods(stream_token, client) > 1:
            logger.error("Found multiple periods, waiting for new write token to begin.")
            time.sleep(INTERVAL)
            continue
        duration = get_livestream_duration(stream_token, client)
        if duration >= end_time + INTERVAL:
            end_time = duration
            with timeit("Making VOD"):
                make_vod(args.livestream, args.vod)
        else:
            logger.info("Stream has not progressed enough, waiting to make vod.")

        logger.info(f"Waiting {INTERVAL} seconds to resume making live2vod")
        time.sleep(INTERVAL)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--livestream", type=str, required=True)
    parser.add_argument("--vod", type=str, required=True)
    args = parser.parse_args()
    main()