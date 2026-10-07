#!/usr/bin/env python3
"""Smoke test for mcp_server.py: initialize, tools/list, tools/call eu4_ping (needs worker.py running)."""
import json
import subprocess
import sys
from pathlib import Path

srv = subprocess.Popen([sys.executable, str(Path(__file__).with_name("mcp_server.py"))],
                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)


def rpc(i, method, params=None):
    srv.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params or {}}) + "\n")
    srv.stdin.flush()
    return json.loads(srv.stdout.readline())


init = rpc(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t"}})
assert init["result"]["serverInfo"]["name"] == "eu4-automation", init
srv.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
tools = [t["name"] for t in rpc(2, "tools/list")["result"]["tools"]]
print("tools:", tools)
ping = rpc(3, "tools/call", {"name": "eu4_ping", "arguments": {}})["result"]
print("eu4_ping isError:", ping["isError"], ping["content"][0]["text"])
saves = rpc(4, "tools/call", {"name": "eu4_list_saves", "arguments": {}})["result"]
print("eu4_list_saves:", len(json.loads(saves["content"][0]["text"])), "files")
bad = rpc(5, "tools/call", {"name": "nope", "arguments": {}})["result"]
assert bad["isError"]
srv.stdin.close()
srv.wait(timeout=10)
print("OK")
