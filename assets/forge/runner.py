"""Build queue for all theme assets, with incremental rebuilds and review sheets.

    python3 -m forge.runner                     # build everything that changed
    python3 -m forge.runner --theme nordic      # one theme (repeatable)
    python3 -m forge.runner --only nordic/sword,egypt/ankh --force
    python3 -m forge.runner --sheets            # only rebuild review sheets
    python3 -m forge.runner --list              # show queue state

Each asset runs in its own Blender (bpy) subprocess. An asset is rebuilt when
the source of its builder, of the theme's helper code, or of forge/ changes.
Output: library/<theme>/<asset>.glb|.jpg|.json and library/<theme>/_review.jpg
(a contact sheet for quick visual review). Logs: /tmp/forge_logs/.
"""
import argparse
import ast
import hashlib
import importlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")
LOGS = "/tmp/forge_logs"
STATUS = os.path.join(LIB, "_status.json")
sys.path.insert(0, ROOT)


def themes():
    d = os.path.join(ROOT, "themes")
    return sorted(f[:-3] for f in os.listdir(d) if f.endswith(".py") and not f.startswith("_"))


def forge_hash():
    h = hashlib.sha1()
    for f in sorted(os.listdir(os.path.join(ROOT, "forge"))):
        if f.endswith(".py") and f not in ("runner.py", "catalog.py", "run_asset.py"):
            h.update(open(os.path.join(ROOT, "forge", f), "rb").read())
    return h.hexdigest()


def theme_assets(theme):
    """[(name, title, source_hash)] in definition order, parsed without bpy."""
    src = open(os.path.join(ROOT, "themes", theme + ".py")).read()
    tree = ast.parse(src)
    assets, helpers = [], []
    for node in tree.body:
        is_asset = isinstance(node, ast.FunctionDef) and any(
            (isinstance(d, ast.Call) and getattr(d.func, "id", "") == "asset") or getattr(d, "id", "") == "asset"
            for d in node.decorator_list)
        (assets if is_asset else helpers).append(node)
    helper_src = "\n".join(ast.unparse(n) for n in helpers)
    fh = forge_hash()
    out = []
    for n in assets:
        h = hashlib.sha1((ast.unparse(n) + helper_src + fh).encode()).hexdigest()[:12]
        out.append((n.name, h))
    return out


def load_status():
    try:
        return json.load(open(STATUS))
    except (OSError, ValueError):
        return {}


def save_status(st):
    os.makedirs(LIB, exist_ok=True)
    json.dump(st, open(STATUS, "w"), indent=1, sort_keys=True)


def build_one(theme, name, timeout):
    os.makedirs(LOGS, exist_ok=True)
    log = os.path.join(LOGS, f"{theme}__{name}.log")
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "-m", "forge.run_asset", theme, name], cwd=ROOT,
                           capture_output=True, text=True, timeout=timeout)
        out = p.stdout + "\n" + p.stderr
    except subprocess.TimeoutExpired as e:
        out = f"TIMEOUT after {timeout}s\n{e.stdout or ''}"
    open(log, "w").write(out)
    for line in out.splitlines():
        if line.startswith("FORGE_RESULT "):
            return True, json.loads(line[13:]), time.time() - t0
        if line.startswith("FORGE_ERROR "):
            return False, json.loads(line[12:]), time.time() - t0
    tail = [ln for ln in out.strip().splitlines() if ln.strip()][-8:]
    return False, dict(error="crashed", tail=tail), time.time() - t0


def contact_sheet(theme, cols=5, cell=360, base=None, out=None):
    from PIL import Image, ImageDraw, ImageFont
    names = [n for n, _ in theme_assets(theme)]
    ims = []
    for n in names:
        p = os.path.join(base or LIB, theme, n + ".jpg")
        meta_p = os.path.join(base or LIB, theme, n + ".json")
        meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
        ims.append((n, Image.open(p).convert("RGB") if os.path.exists(p) else None, meta))
    if not ims:
        return None
    rows = (len(ims) + cols - 1) // cols
    lab = 34
    sheet = Image.new("RGB", (cols * cell, rows * (cell + lab)), (18, 17, 16))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    for i, (n, im, meta) in enumerate(ims):
        x, y = (i % cols) * cell, (i // cols) * (cell + lab)
        if im is not None:
            sheet.paste(im.resize((cell, cell)), (x, y))
        else:
            d.text((x + 10, y + cell // 2), "not built", fill=(200, 80, 60), font=f)
        info = f"{i + 1}. {n}"
        if meta:
            info += f"  {meta['tris'] // 1000}k tri  {meta['glb_kb'] // 1024 or 1}MB"
        d.text((x + 8, y + cell + 8), info, fill=(225, 215, 195), font=f)
    path = out or os.path.join(LIB, theme, "_review.jpg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path, quality=85)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", action="append")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sheets", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--timeout", type=int, default=1500)
    ap.add_argument("--dry", action="store_true", help="build geometry only (fast error check)")
    ap.add_argument("--quick", action="store_true", help="unbaked low-sample preview to /tmp/forge_quick")
    a = ap.parse_args()
    sel = a.theme or themes()
    only = {s.strip() for s in a.only.split(",") if s.strip()}
    st = load_status()
    if a.sheets:
        for t in sel:
            print(contact_sheet(t))
        return

    if a.dry or a.quick:
        os.environ["FORGE_QUICK" if a.quick else "FORGE_DRY"] = "1"
        for t in sel:
            for n, _ in theme_assets(t):
                if only and f"{t}/{n}" not in only and n not in only:
                    continue
                ok, info, secs = build_one(t, n, 600)
                if ok:
                    print(f"dry OK   {t}/{n}  {info['tris']} tris  dims={info['dims_m']}  {secs:.0f}s", flush=True)
                else:
                    print(f"dry FAIL {t}/{n}  {info.get('error')} :: {' | '.join(info.get('tail', [])[-3:])[-500:]}",
                          flush=True)
        if a.quick:
            for t in sel:
                print("quick sheet:", contact_sheet(t, base="/tmp/forge_quick", out=f"/tmp/forge_quick/{t}_quick.jpg"))
        return
    queue = []
    for t in sel:
        for n, h in theme_assets(t):
            key = f"{t}/{n}"
            if only and key not in only and n not in only:
                continue
            fresh = st.get(key, {}).get("hash") == h and st[key].get("ok")
            if a.list:
                print(f"{'ok ' if fresh else '...'} {key}")
            elif a.force or not fresh:
                queue.append((t, n, h))
    if a.list:
        return
    print(f"queue: {len(queue)} asset(s)", flush=True)
    done_themes = []
    for i, (t, n, h) in enumerate(queue):
        ok, info, secs = build_one(t, n, a.timeout)
        key = f"{t}/{n}"
        if ok:
            st[key] = dict(hash=h, ok=True, secs=round(secs), tris=info["tris"], kb=info["glb_kb"])
            print(f"[{i + 1}/{len(queue)}] OK   {key}  {secs:.0f}s  {info['tris']} tris  {info['glb_kb']}KB",
                  flush=True)
        else:
            st[key] = dict(hash=h, ok=False, error=info.get("error"))
            tail = " | ".join(info.get("tail", [])[-3:])
            print(f"[{i + 1}/{len(queue)}] FAIL {key}  {info.get('error')}  :: {tail[-400:]}", flush=True)
        save_status(st)
        if t not in done_themes and (i + 1 == len(queue) or queue[i + 1][0] != t):
            done_themes.append(t)
            print(f"sheet: {contact_sheet(t)}", flush=True)


if __name__ == "__main__":
    main()
