import httpx
from posting import Posting


def on_response(response: httpx.Response, posting: Posting) -> None:
    if response.status_code.ok:
        posting.set_variable("ZONE_ID", response.json()["result"][0]["id"])

    return None
