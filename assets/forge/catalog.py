"""Write library/README.md: a catalogue of every built asset (from the *.json metas).

    python3 -m forge.catalog
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")

THEMES = [
    ("nordic", "Nordic / Viking age", "c. 800-1050 AD. Weapons, armour, drinking gear, tools."),
    ("viking_hall", "Viking hall - modular kit", "Building kit for a longhouse / mead hall (see metrics below)."),
    ("egypt", "Ancient Egypt", "New Kingdom. Regalia, amulets, vessels, a senet board, a papyrus with real hieroglyphs."),
    ("jade_dynasty", "Jade Dynasty", "Modern imperial China: polished jade, gold, black lacquer, celadon."),
    ("greece", "Greece / Olympus", "Archaic-Classical. Hoplite gear, painted pottery, divine attributes."),
    ("paris_1940", "Occupied Paris 1940-44", "A comfortable bourgeois apartment: devices, tableware, furniture."),
    ("aztec", "Aztec jungle", "Mexica, c. 1400-1521. Obsidian weapons, mosaics, featherwork, daily tools."),
]

KIT_NOTES = """
### Kit metrics (viking_hall)

| Rule | Value |
|---|---|
| Grid | 2 m along the hall (X). Span 8 m, outer wall lines at y = -4 / +4 |
| Stone plinth | z 0 - 0.5 (`foundation_2m`, `foundation_corner`) |
| Floor level | z = 0.5 (`floor_*_2x2`, top surface at the pivot) |
| Walls | 2.5 m, base on the plinth, top plate at z = 3.0 |
| Roof | 45 deg, 0.6 m eave overhang, ridge at z = 7.0. Place roof pieces at z = 3.0 |
| Hall posts | two rows at y = +-2, 4.0 m tall on the floor; purlins (`beam_2m`) on top at z = 4.5 |
| Door | `door_plank` hinges at local (0.57, 0, 0.22) of `wall_plank_door_2m` |
| Opposite roof slope | `roof_thatch_2m` rotated 180 deg about Z, shifted +2 m in X |

Pivots sit exactly on the snapping point (module start on the wall centre line,
or footprint centre for posts and props).
"""


def main():
    lines = ["# 3D asset library", "",
             "Procedurally generated, game-ready glTF 2.0 assets (PBR metallic-roughness, one baked texture set "
             "per asset: base colour, ORM, tangent-space normal; real-world scale in metres; +Y up).", "",
             "Everything is regenerated from code: `python3 -m forge.runner` (see `assets/forge/`).", ""]
    total = 0
    for key, title, blurb in THEMES:
        d = os.path.join(LIB, key)
        if not os.path.isdir(d):
            continue
        metas = []
        for f in sorted(os.listdir(d)):
            if f.endswith(".json") and not f.startswith("_"):
                metas.append(json.load(open(os.path.join(d, f))))
        if not metas:
            continue
        total += len(metas)
        lines += [f"## {title}", "", blurb, "", f"![{title}]({key}/_review.jpg)", ""]
        lines += ["| Asset | File | Size (m) | Triangles | Texture | GLB |", "|---|---|---|---|---|---|"]
        for m in metas:
            dims = " x ".join(f"{x:.2f}" for x in m["dims_m"])
            lines.append(f"| {m['title']} | `{key}/{m['name']}.glb` | {dims} | {m['tris']:,} | {m['texture']} px | "
                         f"{m['glb_kb'] / 1024:.1f} MB |")
        lines.append("")
        if key == "viking_hall":
            lines.append(KIT_NOTES)
    lines += ["## Engine notes", "",
              "- **Unity**: glTFast or UnityGLTF. **Unreal 5**: built-in glTF importer (Interchange). "
              "**Godot 4**: native. **three.js / Babylon**: GLTFLoader.",
              "- Normal maps are OpenGL-style (+Y). Flip green for DirectX-convention pipelines.",
              "- Glass, liquids and embers use separate untextured materials (transmission / emission).", "",
              f"_{total} assets._", ""]
    open(os.path.join(LIB, "README.md"), "w").write("\n".join(lines))
    print(f"catalogue: {total} assets")


if __name__ == "__main__":
    main()
