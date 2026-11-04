#!/usr/bin/env python3
"""
Retry the instances listed in main/citylist-hs.json (out of service) and move
the ones that answer again back into main/citylist.json.

Each instance is checked exactly like the live check (check_instances.check):
get_scope.php, get_issues.php, the latest panel image, HTTPS and CORS. An
instance that passes every check has its hs_since / hs_reason fields dropped and
is appended to citylist.json (and removed from citylist-hs.json).

Writes a Markdown report (GitHub step summary when available) and, when at least
one instance came back, sets moved=1 in GITHUB_OUTPUT so the workflow opens a PR.
The JSON files keep their exact formatting (3-space indent), so unchanged entries
stay byte-for-byte identical and the diff only shows the moved instances.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import check_instances  # noqa: E402  (reuses the live check logic)

HERE = os.path.dirname(__file__)
CITYLIST = os.path.join(HERE, "..", "..", "main", "citylist.json")
CITYLIST_HS = os.path.join(HERE, "..", "..", "main", "citylist-hs.json")
HS_FIELDS = ("hs_since", "hs_reason")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    # Same style as the hand-written files: 3-space indent, no space after ":".
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=3, separators=(",", ":"))
        f.write("\n")


def report(lines):
    text = "\n".join(lines) + "\n"
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(text)


def set_output(name, value):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write("%s=%s\n" % (name, value))


def main():
    cities = load(CITYLIST)
    hs = load(CITYLIST_HS)
    if not hs:
        report(["## Réessai des instances HS", "", "Aucune instance hors service à réessayer."])
        set_output("moved", "0")
        return 0

    results = [(name, conf, check_instances.check(name, conf)) for name, conf in hs.items()]
    recovered = [(name, conf) for name, conf, r in results if r["ok"]]

    for name, conf in recovered:
        cities[name] = {k: v for k, v in conf.items() if k not in HS_FIELDS}
        del hs[name]

    if recovered:
        save(CITYLIST, cities)
        save(CITYLIST_HS, hs)

    lines = ["## Réessai des instances HS : %d remontée(s) sur %d" % (len(recovered), len(results)), "",
             "| Instance | Résultat |", "|---|---|"]
    moved_names = {name for name, _ in recovered}
    for name, conf, r in sorted(results, key=lambda t: (t[2]["ok"], t[0])):
        status = "**remontée dans citylist.json**" if name in moved_names \
            else "toujours HS : " + "; ".join(r["problems"]).replace("|", "/")
        lines.append("| %s | %s |" % (name, status))
    if recovered:
        lines += ["", "Instances remontées : " + ", ".join(sorted(moved_names)) + "."]
    report(lines)
    set_output("moved", "1" if recovered else "0")
    set_output("names", ", ".join(sorted(moved_names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
