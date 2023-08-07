"""Procedures used to work with the various bio-informatics cli
commands"""
import sys
import json
import subprocess
from uuid import uuid4
from datetime import datetime
from typing import Dict, Optional, Tuple, Union, Sequence


from redis.client import Redis

def queue_cmd(conn: Redis,
              job_queue: str,
              cmd: Union[str, Sequence[str]],
              email: Optional[str] = None,
              env: Optional[dict] = None) -> str:
    """Given a command CMD; (optional) EMAIL; and a redis connection CONN, queue
it in Redis with an initial status of 'queued'.  The following status codes
are supported:

    queued:  Unprocessed; Still in the queue
    running: Still running
    success: Successful completion
    error:   Erroneous completion

Returns the name of the specific redis hash for the specific task.

    """
    if not conn.ping():
        raise RedisConnectionError
    unique_id = ("cmd::"
                 f"{datetime.now().strftime('%Y-%m-%d%H-%M%S-%M%S-')}"
                 f"{str(uuid4())}")
    conn.rpush(job_queue, unique_id)
    for key, value in {
            "cmd": json.dumps(cmd), "result": "", "status": "queued"}.items():
        conn.hset(name=unique_id, key=key, value=value)
    if email:
        conn.hset(name=unique_id, key="email", value=email)
    if env:
        conn.hset(name=unique_id, key="env", value=json.dumps(env))
    return unique_id

def run_cmd(cmd: str, success_codes: Tuple = (0,), env: str = None) -> Dict:
    """Run CMD and return the CMD's status code and output as a dict"""
    parsed_cmd = json.loads(cmd)
    parsed_env = (json.loads(env) if env is not None else None)
    results = subprocess.run(
        parsed_cmd, capture_output=True, shell=isinstance(parsed_cmd, str),
        check=False, env=parsed_env)
    out = str(results.stdout, 'utf-8')
    if results.returncode not in success_codes:  # Error!
        out = str(results.stderr, 'utf-8')
    return {"code": results.returncode, "output": out}

def run_async_cmd(
        conn: Redis, job_queue: str, cmd: Union[str, Sequence[str]],
        email: Optional[str] = None, env: Optional[dict] = None) -> str:
    """A utility function to call `gn3.commands.queue_cmd` function and run the
    worker in the `one-shot` mode."""
    cmd_id = queue_cmd(conn, job_queue, cmd, email, env)
    subprocess.Popen([f"{sys.executable}", "-m", "sheepdog.worker"]) # pylint: disable=[consider-using-with]
    return cmd_id
