from typing import Any, Dict, Optional
import json
import urllib.request

from summaryflow_v4 import summarize_message


def route_message(payload: Dict[str, Any], use_http: bool = False, base_url: str = "http://127.0.0.1:8000") -> Dict[str, Any]:
    if use_http:
        url = f"{base_url}/summarize"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    return summarize_message(payload)
