import os
import json
from datetime import datetime

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
