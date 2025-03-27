
import os
import json
import tempfile
import time
from loguru import logger

from e2e_test.common import get_client, set_message, finalize, content_info

def crawl(tok: str, config: str) -> None:
    logger.debug(f"Write token: {tok}")
    with tempfile.NamedTemporaryFile() as fp:
        print(fp.name)
        finished = False
        logger.debug(f"Awaiting crawl")
        lro = search_update(tok, fp, config)
        logger.info(f"lro handle: {lro}")
        while not finished:
            state = status(tok, lro, fp.name, config)
            finished = state == "terminated"
            time.sleep(7)
    set_message(tok, "test crawl", config)
    finalize(tok, config)

def search_update(tok: str, temp_file: any, config: str) -> str:
    print(os.path.exists(temp_file.name))
    cmd = [get_client(), 'content', 'bitcode', 'call', tok, 'search_update', '\"\"', temp_file.name, '--config', config, '--finalize=false', '--post']
    print(' '.join(cmd))
    os.popen(' '.join(cmd)).read()
    print(os.path.exists(temp_file.name))
    with open(temp_file.name, 'r') as tf:
        print(tf.read())
    lro = json.load(temp_file)
    return json.dumps(lro)

def status(tok: str, lro: str, f: str, config: str) -> str:
    cmd = [get_client(), 'content', 'bitcode', 'call', tok, 'crawl_status', "'" + lro + "'", f, '--config', config, '--post']
    os.popen(' '.join(cmd)).read()
    with open(f, 'r') as ff:
        status = ff.read()
    logger.info(status)
    return json.loads(status)["state"]