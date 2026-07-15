from urllib.request import Request, urlopen
from urllib.error import URLError
import json as _json


def update_worklist_status(portal_url: str, api_key: str, accession_number: str, status: str, study_uid: str = ""):
    data = {"accession_number": accession_number, "status": status}
    if study_uid:
        data["study_instance_uid"] = study_uid
    body = _json.dumps(data).encode()
    req = Request(
        f"{portal_url.rstrip('/')}/api/worklist/status",
        data=body,
        headers={
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except URLError:
        return False
