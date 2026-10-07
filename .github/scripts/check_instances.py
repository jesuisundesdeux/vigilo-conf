#!/usr/bin/env python3
"""
Check that every instance listed in main/citylist.json answers.

For each instance: GET <api_path>/get_scope.php?scope=<scope> must return the
scope as JSON, and GET <api_path>/get_issues.php?scope=<scope>&count=1 gives the
date of the latest observation (activity indicator only).

Writes a Markdown report (GitHub step summary when available) and exits with 1
when at least one instance is down.
"""
import concurrent.futures
import datetime
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

CITYLIST = os.path.join(os.path.dirname(__file__), "..", "..", "main", "citylist.json")
TIMEOUT = 20
TRIES = 3


def fetch_json(url, context=None):
    last_error = None
    for attempt in range(TRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "vigilo-conf instance check"})
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=context) as resp:
                body = resp.read().decode("utf-8", "replace")
            try:
                return json.loads(body)
            except ValueError:
                raise RuntimeError("not JSON: " + body.strip().replace("\n", " ")[:80])
        except urllib.error.HTTPError as e:
            last_error = "HTTP %d" % e.code
        except urllib.error.URLError as e:
            last_error = str(e.reason)
        except Exception as e:  # timeouts, SSL, bad JSON...
            last_error = str(e) or e.__class__.__name__
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(last_error)


def check(name, conf):
    base = conf["api_path"].rstrip("/")
    scope = conf["scope"]
    result = {"name": name, "api_path": conf["api_path"], "scope": scope, "prod": conf.get("prod")}
    try:
        data = fetch_json("%s/get_scope.php?scope=%s" % (base, scope))
        if not isinstance(data, dict) or data.get("status", 0) != 0 or "display_name" not in data:
            raise RuntimeError("unexpected answer: " + json.dumps(data)[:80])
        result["ok"] = True
        result["version"] = data.get("backend_version", "?")
    except RuntimeError as e:
        result["ok"] = False
        result["error"] = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            # browsers refuse it too, but tell whether the API still answers behind it
            try:
                fetch_json("%s/get_scope.php?scope=%s" % (base, scope), ssl._create_unverified_context())
                result["error"] += " (the API answers without certificate check: fix the certificate)"
            except RuntimeError as e2:
                result["error"] += " (no API behind either: %s)" % e2
        return result
    try:
        issues = fetch_json("%s/get_issues.php?scope=%s&count=1" % (base, scope))
        if issues:
            result["last"] = datetime.datetime.fromtimestamp(int(issues[0]["time"]), datetime.timezone.utc).date().isoformat()
        else:
            result["last"] = "none"
    except Exception as e:
        result["last"] = "? (%s)" % e
    return result


def main():
    with open(CITYLIST, encoding="utf-8") as f:
        cities = json.load(f)
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda item: check(*item), cities.items()))
    down = [r for r in results if not r["ok"]]

    lines = ["## Vigilo instances: %d OK, %d down" % (len(results) - len(down), len(down)), "",
             "| Instance | prod | API | Status | Backend | Latest observation |",
             "|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: (r["ok"], r["name"])):
        status = "OK" if r["ok"] else "**DOWN**: " + r["error"].replace("|", "/")
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            r["name"], r["prod"], r["api_path"], status, r.get("version", ""), r.get("last", "")))
    report = "\n".join(lines) + "\n"
    print(report)
    print("JSON:" + json.dumps(results, ensure_ascii=False))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report)
    return 1 if down else 0


if __name__ == "__main__":
    sys.exit(main())
