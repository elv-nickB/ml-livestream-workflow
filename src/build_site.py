
import os
import json
from tqdm import tqdm

from e2e_test.common import *

def get_link(id: str, config: str) -> dict:
    cmd = [get_client(), 'content', 'describe', id, '--config', config]
    try:
        res = os.popen(' '.join(cmd)).read()
        data = json.loads(res)
    except json.JSONDecodeError as e:
        print(f"error with {id}")
        print(res)
        print(cmd)
        raise e
    hash = data["hash"]
    return {"/": f"/qfab/{hash}/meta"}

def build_site(tok: str, message: str, config: str):
    links = {}
    site_map = get_metadata(tok, "/site_map/searchables", resolve=False, config=config)
    for k, link in tqdm(site_map.items()):
        hash = link["/"].split('/')[2]
        qid = content_info(hash, config)["id"]
        l = get_link(qid, config)
        links[k] = l
    site_data = json.dumps({"site_map": {"searchables": links}})
    merge_metadata(tok, site_data, config)
    set_message(tok, message, config)
    print(f"finalizing {tok}")
    finalize(tok, config)