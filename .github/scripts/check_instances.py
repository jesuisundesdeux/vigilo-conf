#!/usr/bin/env python3
"""
Check that every instance listed in main/citylist.json works for app.vigilo.city.

For each instance, the calls made by the web app are reproduced:
- get_scope.php?scope=<scope> must return the scope as JSON
- get_issues.php?scope=<scope> (the full list, as loaded by the app) must
  return a JSON list in a reasonable time
- the panel image of the latest observation must load
- the API must be served over HTTPS (app.vigilo.city is HTTPS: a browser
  blocks plain HTTP calls) with the Access-Control-Allow-Origin header (CORS)

An instance is "down" when one of these fails. Writes a Markdown report (GitHub
step summary when available) and exits with 1 when at least one instance is down.
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
ISSUES_TIMEOUT = 60
SLOW = 15
TRIES = 3
ORIGIN = "https://app.vigilo.city"


def fetch(url, timeout=TIMEOUT, context=None):
    """(body bytes, headers, seconds); RuntimeError with a short reason otherwise"""
    last_error = None
    for attempt in range(TRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "vigilo-conf instance check", "Origin": ORIGIN})
            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
                body = resp.read()
                return body, resp.headers, time.monotonic() - start
        except urllib.error.HTTPError as e:
            last_error = "HTTP %d" % e.code
        except urllib.error.URLError as e:
            last_error = str(e.reason)
        except Exception as e:  # timeouts, SSL...
            last_error = str(e) or e.__class__.__name__
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(last_error)


def parse_json(body):
    text = body.decode("utf-8", "replace")
    try:
        return json.loads(text)
    except ValueError:
        raise RuntimeError("not JSON: " + text.strip().replace("\n", " ")[:80])


def has_cors(headers):
    return headers.get("Access-Control-Allow-Origin") in ("*", ORIGIN)


def check(name, conf):
    base = conf["api_path"].rstrip("/")
    scope = conf["scope"]
    result = {"name": name, "api_path": conf["api_path"], "scope": scope, "prod": conf.get("prod"), "problems": []}
    problems = result["problems"]

    if not base.startswith("https://"):
        problems.append("API not served over HTTPS (blocked by browsers)")

    # scope
    try:
        body, headers, _ = fetch("%s/get_scope.php?scope=%s" % (base, scope))
        data = parse_json(body)
        if not isinstance(data, dict) or "display_name" not in data:
            raise RuntimeError("unexpected answer: " + json.dumps(data)[:80])
        result["version"] = data.get("backend_version", "?")
        if not has_cors(headers):
            problems.append("get_scope.php without CORS header")
    except RuntimeError as e:
        problems.append("get_scope.php: %s" % e)
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            try:
                fetch("%s/get_scope.php?scope=%s" % (base, scope), context=ssl._create_unverified_context())
                problems.append("(the API answers without certificate check: fix the certificate)")
            except RuntimeError:
                pass
        result["ok"] = False
        return result

    # observations, as loaded by the app
    try:
        body, headers, seconds = fetch("%s/get_issues.php?scope=%s" % (base, scope), timeout=ISSUES_TIMEOUT)
        issues = parse_json(body)
        if not isinstance(issues, list):
            raise RuntimeError("unexpected answer: " + json.dumps(issues)[:80])
        result["count"] = len(issues)
        result["issues_time"] = round(seconds, 1)
        if seconds > SLOW:
            problems.append("get_issues.php very slow (%.0f s)" % seconds)
        if not has_cors(headers):
            problems.append("get_issues.php without CORS header")
        if issues:
            latest = max(issues, key=lambda i: int(i.get("time") or 0))
            result["last"] = datetime.datetime.fromtimestamp(int(latest["time"]), datetime.timezone.utc).date().isoformat()
            try:
                img, headers, _ = fetch("%s/generate_panel.php?s=150&token=%s" % (base, latest["token"]))
                if not img[:3] == b"\xff\xd8\xff" and not img[:4] == b"\x89PNG":
                    problems.append("generate_panel.php does not return an image")
            except RuntimeError as e:
                problems.append("generate_panel.php: %s" % e)
        else:
            result["last"] = "none"
    except RuntimeError as e:
        problems.append("get_issues.php: %s" % e)

    result["ok"] = not problems
    return result


def main():
    with open(CITYLIST, encoding="utf-8") as f:
        cities = json.load(f)
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda item: check(*item), cities.items()))
    down = [r for r in results if not r["ok"]]

    lines = ["## Vigilo instances: %d OK, %d down" % (len(results) - len(down), len(down)), "",
             "| Instance | prod | API | Status | Backend | Observations | Latest | Load time |",
             "|---|---|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: (r["ok"], r["name"])):
        status = "OK" if r["ok"] else "**DOWN**: " + "; ".join(r["problems"]).replace("|", "/")
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["name"], r["prod"], r["api_path"], status, r.get("version", ""), r.get("count", ""),
            r.get("last", ""), ("%s s" % r["issues_time"]) if "issues_time" in r else ""))
    report = "\n".join(lines) + "\n"
    print(report)
    print("JSON:" + json.dumps(results, ensure_ascii=False))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report)
    payload = {
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {"total": len(results), "ok": len(results) - len(down), "down": len(down)},
        "instances": results,
    }
    with open("check_result.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return 1 if down else 0


if __name__ == "__main__":
    sys.exit(main())
