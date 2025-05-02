import os
import json
from datetime import datetime
import subprocess
import time
from loguru import logger
from requests import HTTPError
from elv_client_py import ElvClient

def edit(id: str, config: str) -> str:
    cmd = [get_client(), 'content', 'edit', id, '--config', config]
    stream = os.popen(' '.join(cmd))
    tok = json.loads(stream.read())['q']['write_token']
    return tok

def merge_metadata(tok: str, data: str, config: str) -> str:
    cmd = [get_client(), 'content', 'meta', 'merge', tok, f"'{data}'", '--config', config]
    return os.popen(' '.join(cmd)).read()

def set_metadata(tok: str, data: str, path: str, config: str) -> str:
    cmd = [get_client(), 'content', 'meta', 'set', tok, f"'{data}'", f'--meta-path={path}', '--config', config]
    return os.popen(' '.join(cmd)).read()

def get_metadata(id: str, path: str, select: str="/", resolve: bool=False, config: str=None) -> dict:
    cmd = [get_client(), 'content', 'meta', 'get', id, path, f'--resolve={str(resolve).lower()}', '--select', select, '--config', config]
    res = os.popen(' '.join(cmd)).read()
    try:
        res = json.loads(res)
    except json.JSONDecodeError:
        print(f"Failed to get metadata for {id} at {path}")
        return None
    return res

def content_info(id: str, config: str) -> dict:
    cmd = [get_client(), 'content', 'describe', id, '--config', config]
    return json.loads(os.popen(' '.join(cmd)).read())

def set_message(tok: str, message: str, config: str) -> str:
    merge_metadata(tok, json.dumps({"commit": {"message": message, "timestamp": datetime.now().isoformat(timespec='microseconds') + 'Z'}}), config)

def finalize(tok: str, config: str) -> str:
    cmd = [get_client(), 'content', 'finalize', tok, '--config', config]
    return os.popen(' '.join(cmd)).read()

def get_client() -> str:
    if os.getenv('FABRIC_CLIENT'):
        return os.getenv('FABRIC_CLIENT')
    else:
        return 'qfab_cli'
    
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

def get_livestream_duration(live_token: str, client: ElvClient) -> int:
    try:
        periods = client.content_object_metadata(write_token=live_token, metadata_subtree="live_recording/recordings/live_offering")
    except HTTPError as e:
        logger.error(e)
        logger.error("Error retrieving duration of livestream. Returning 0 seconds.")
        return 0
    if len(periods) == 0:
        return 0
    #assert len(periods) == 1
    if 'video' not in periods[0]['finalized_parts_info']:
        return 0
    num_parts = periods[-1]['finalized_parts_info']['video']['n_parts']
    part_duration = 30
    return max(0, (num_parts - 1) * part_duration)

def get_num_periods(live_token: str, client: ElvClient) -> int:
    return len(client.content_object_metadata(metadata_subtree='live_recording/recordings/live_offering', resolve_links=False, write_token=live_token))

def get_livestream_token(qid: str, client: ElvClient) -> str:
    return client.content_object_metadata(object_id=qid, metadata_subtree="live_recording/status/edge_write_token")

class timeit():
    def __init__(self, msg: str):
        self.msg = msg

    def __enter__(self):
        self.start = time.time()
        logger.info(f"Starting {self.msg}")

    def __exit__(self, *args):
        logger.info(f"{self.msg} took {time.time() - self.start} seconds")