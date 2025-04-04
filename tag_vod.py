import requests
from copy import deepcopy
from common_ml.utils.metrics import timeit
import time
import subprocess
import argparse
import json
import threading

from src.build_site import build_site
from src.crawl import crawl
from src.common import finalize
from src.external_tag_subset import trim_tags

from config import config

content = "iq__QBn6dV7QKnpou1Ro3p4YZhhVXwL"
index = "iq__32LqQRXfVtmeyA8Yi1fAMGbjcu7N"

host_tag = "http://localhost:8086"
host_search = "http://localhost:8085"

tag_request = {"features":{"shot":{}, "asr": {"stream": "audio_1"}}}

# interval to do tagging
tag_interval = 10 * 60

finish_time = 120 * 60

# frequency to do searches
search_freq = 30

def get_auth(config: str, qhit: str) -> str:
    cmd = f"qfab_cli content token create {qhit} --update --config {config}"
    out = subprocess.run(cmd, shell=True, check=True, capture_output=True).stdout.decode("utf-8")
    token = json.loads(out)["bearer"]
    return token

def get_write_token(qhit: str, config: str) -> str:
    cmd = f"qfab_cli content edit {qhit} --config {config}"
    out = subprocess.run(cmd, shell=True, check=True, capture_output=True).stdout.decode("utf-8")
    write_token = json.loads(out)["q"]["write_token"]
    return write_token

def upload_external(auth: str, file: str):
    url = f"{host_tag}/{content}/upload_tags?authorization={auth}"
    with open(file, "rb") as f:
        response = requests.post(url, files={"file": f})
    if response.status_code != 200:
        raise Exception(f"Error in uploading external tags: {response.text}")

def do_tagging(auth: str, config: str, end_time: int):
    #request = deepcopy(tag_request)
    request = tag_request
    request["end_time"] = end_time
    response = requests.post(f"{host_tag}/{content}/tag?authorization={auth}", json=tag_request)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        raise Exception(f"Error in tagging: {response.text}")
    done = False
    with timeit("Awaiting tagging completion"):
        while not done:
            status = requests.get(f"{host_tag}/{content}/status?authorization={auth}").json()
            print(json.dumps(status, indent=2) + "\n")
            done = True
            for stream in status:
                for feature in status[stream]:
                    if status[stream][feature]['status'] != "Completed":
                        done = False
                        break
                    elif status[stream][feature]['status'] == "Failed":
                        raise Exception(f"Error in tagging: {status[stream][feature]['error']}")
            time.sleep(20)
    with timeit("Finalizing"):
        write_token = get_write_token(content, config)
        response = requests.post(f"{host_tag}/{content}/finalize?authorization={auth}&write_token={write_token}")
        if response.status_code == 200:
            print(response.json())
        else:
            raise Exception(f"Error in finalizing: {response.text}")
        finalize(write_token, config)

def update_search(qid: str, config: str, auth: str):
    write_token = get_write_token(qid, config)
    with timeit("updating site"):
        build_site(write_token, "built site for testing", config)
    time.sleep(3)
    write_token = get_write_token(qid, config)
    with timeit("crawling fabric index"):
        crawl(write_token, config)
    time.sleep(3)
    with timeit("updating vector search index"):
        update_url = f"{host_search}/q/{index}/search_update?authorization={auth}"
        response = requests.get(update_url).json()
        print("-----SEARCH-----\n" + json.dumps(response, indent=2) + "\n")
        status_url = f"{host_search}/q/{index}/update_status?authorization={auth}"
        done = False
        while not done:
            status = requests.get(status_url).json()
            done = status["status"] == "finished"
            print(json.dumps(status, indent=2) + "\n")
            time.sleep(5)

def do_search(auth: str):
    search_url = f"{host_search}/q/{index}/rep/search?authorization={auth}"
    params = {"terms": "an impressive play", "max_total": 50, "limit": 1}
    with timeit("searching"):
        response = requests.get(search_url, params=params)
    print(response.json())

def search_loop(auth):
    while True:
        do_search(auth)
        time.sleep(search_freq)

def main():
    auth = get_auth(args.config, content)
    end_time = 0
    started_search = False
    while True:
        end_time += tag_interval
        if end_time > finish_time:
            print('done')
            break
        trim_tags(config['external_tags'].split('.')[0] + "_master.json", config['external_tags'], end_time * 1000)
        with timeit("Running full pipeline"):
            upload_external(auth, config['external_tags'])
            do_tagging(auth, args.config, end_time)
            #update_search(index, args.config, auth)
        if not started_search:
            threading.Thread(target=search_loop, args=(auth,), daemon=True).start()
            time.sleep(5)
            started_search = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    args = parser.parse_args()
    main()