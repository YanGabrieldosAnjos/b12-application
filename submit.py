import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


def main():
    signing_secret = os.environ["B12_SIGNING_SECRET"]
    github_server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    github_repository = os.environ["GITHUB_REPOSITORY"]
    github_run_id = os.environ["GITHUB_RUN_ID"]

    now = datetime.now(timezone.utc)

    payload = {
        "action_run_link": f"{github_server}/{github_repository}/actions/runs/{github_run_id}",
        "email": os.environ["B12_EMAIL"],
        "name": os.environ["B12_NAME"],
        "repository_link": f"{github_server}/{github_repository}",
        "resume_link": os.environ["B12_RESUME_LINK"],
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z",
    }

    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    signature = hmac.new(
        signing_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    req = urllib.request.Request(
        "https://b12.io/apply/submission",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": f"sha256={signature}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            response_body = json.loads(resp.read().decode("utf-8"))
            print(f"Response: {response_body}")
            if response_body.get("success"):
                print(f"Receipt: {response_body['receipt']}")
            else:
                print("Submission was not successful.", file=sys.stderr)
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode('utf-8')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
