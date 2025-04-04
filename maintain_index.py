import argparse
import json
import requests
import time
from loguru import logger

from elv_client_py import ElvClient

from src.common import timeit, get_write_token, get_auth
from src.build_site import build_site
from src.crawl import crawl
from config import config

def update_search(qid: str, cli_config: str, auth: str):
    write_token = get_write_token(qid, cli_config)
    with timeit("updating site"):
        build_site(write_token, "built site for testing", cli_config)
    time.sleep(3)
    write_token = get_write_token(qid, cli_config)
    with timeit("crawling fabric index"):
        crawl(write_token, cli_config)
    time.sleep(3)
    with timeit("updating vector search index"):
        update_url = f"{config['search_host']}/q/{qid}/search_update?authorization={auth}"
        response = requests.get(update_url).json()
        logger.debug("-----SEARCH-----\n" + json.dumps(response, indent=2) + "\n")
        status_url = f"{config['search_host']}/q/{qid}/update_status?authorization={auth}"
        done = False
        while not done:
            status = requests.get(status_url).json()
            done = status["status"] == "finished"
            if done:
                break
            print(json.dumps(status, indent=2) + "\n")
            time.sleep(3)

def main():
    auth = get_auth(args.config, args.index)
    client = ElvClient.from_configuration_url(config["fabric_url"], auth)
    qid = args.vod
    if args.right_away:
        update_search(args.index, args.config, auth)
    latest_hash = client.content_object(object_id=qid)["hash"]
    while True:
        current_hash = client.content_object(object_id=qid)["hash"]
        if current_hash == latest_hash:
            logger.info("No new version detected")
            time.sleep(10)
            continue
        update_search(args.index, args.config, auth)
        latest_hash = current_hash
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--index", type=str, required=True)
    parser.add_argument("--vod", type=str, required=True)
    parser.add_argument("--right_away", action="store_true")
    args = parser.parse_args()
    main()