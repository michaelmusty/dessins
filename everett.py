"""
https://chatgpt.com/c/68858ea5-2ab4-832a-8019-e4b5edcf1288

https://beta.lmfdb.org/Belyi/7T6/4.2.1/3.2.2/3.2.2/a/
pdm run python everett.py --white "(1,6,5,3)(4,7)" --black "(1,2,3)(4,5)(6,7)"

https://beta.lmfdb.org/Belyi/8T38/4.2.2/3.3.1.1/3.3.2/a/
pdm run python everett.py --white "(1,4,5,8)(2,7)(3,6)" --black "(1,2,3)(5,6,7)"

https://beta.lmfdb.org/Belyi/9T33/5.2.2/4.3.2/3.2.2.1.1/a/
pdm run python everett.py --white "(1,2,3,4,5)(6,7)(8,9)" --black "(1,3,9)(2,6,7,8)(4,5)"
"""

import argparse
import math
import re
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


# ------------ setup functions ------------
def parse_cycles(s):
    s = s.replace(" ", "")
    return [
        [int(x) for x in part.split(",") if x] for part in re.findall(r"\(([^)]+)\)", s)
    ]


def ensure_singletons(cycles, labels):
    present = {label for cyc in cycles for label in cyc}
    for label in labels:
        if label not in present:
            cycles.append([label])
    return cycles


def rotate_cycle(cycle, first):
    if first not in cycle:
        return cycle
    i = cycle.index(first)
    return cycle[i:] + cycle[:i]


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate Everett diagrams from permutation cycles"
    )
    parser.add_argument(
        "--white", 
        default="(1,6,5,3)(4,7)",
        help="White permutation cycles (default: (1,6,5,3)(4,7))"
    )
    parser.add_argument(
        "--black", 
        default="(1,2,3)(4,5)(6,7)",
        help="Black permutation cycles (default: (1,2,3)(4,5)(6,7))"
    )
    args = parser.parse_args()

    # ------------ permutations ---------------
    sigma0 = args.white
    sigma1 = args.black
    cw = parse_cycles(sigma0)
    cb = parse_cycles(sigma1)
    labels = {label for c in cw + cb for label in c}
    ensure_singletons(cw, labels)
    ensure_singletons(cb, labels)
    cw.sort(key=min)
    cb.sort(key=min)
    cw[0] = rotate_cycle(cw[0], 1)

    vertices = {}
    wmap, bmap = {}, {}
    for idx, cyc in enumerate(cw, 1):
        vid = f"w{idx}"
        vertices[vid] = {"cycle": cyc, "deg": len(cyc), "color": "white"}
        for label in cyc:
            wmap[label] = vid
    for idx, cyc in enumerate(cb, 1):
        vid = f"b{idx}"
        vertices[vid] = {"cycle": cyc, "deg": len(cyc), "color": "black"}
        for label in cyc:
            bmap[label] = vid

    edges = {label: {"white": wmap[label], "black": bmap[label]} for label in labels}


    def port_angle(v, idx):
        return idx * 2 * math.pi / vertices[v]["deg"]


    port_index = {
        v: {lab: i for i, lab in enumerate(vertices[v]["cycle"])} for v in vertices
    }

    # -------- drawing params -----------
    L = 1.4
    vertex_r = 0.22
    stub_len = vertex_r
    pos = {"w1": (0, 0)}
    orient = {"w1": 0.0}
    visited = set()
    straight = []
    curves = []
    stubs = []


    def unit(a):
        return math.cos(a), math.sin(a)


    def place_vertex(v_new, origin, dir_angle, lab):
        dx, dy = unit(dir_angle)
        pos[v_new] = (origin[0] + L * dx, origin[1] + L * dy)
        k = port_index[v_new][lab]
        orient[v_new] = (dir_angle + math.pi) - port_angle(v_new, k)


    def draw_edge(v, pidx):
        lab = vertices[v]["cycle"][pidx]
        if lab in visited:
            return
        visited.add(lab)
        w, b = edges[lab]["white"], edges[lab]["black"]
        u = b if v == w else w
        theta_out = orient[v] + port_angle(v, pidx)
        P0 = pos[v]
        Uout = unit(theta_out)
        P0s = (P0[0] + stub_len * Uout[0], P0[1] + stub_len * Uout[1])
        stubs.append((P0, P0s))
        if u not in pos:
            place_vertex(u, P0, theta_out, lab)
            straight.append((P0s, pos[u], lab))
        else:
            kin = port_index[u][lab]
            theta_u_out = orient[u] + port_angle(u, kin)  # outgoing direction at u
            Uin = unit(theta_u_out)
            Pin = pos[u]
            P3s = (Pin[0] + stub_len * Uin[0], Pin[1] + stub_len * Uin[1])
            stubs.append((Pin, P3s))
            dist = math.dist(P0s, P3s)
            # angle differences for scaling d
            cw_angle = (theta_out - theta_u_out) % (2 * math.pi)
            ccw_angle = (theta_u_out - theta_out) % (2 * math.pi)
            alpha = min(cw_angle, ccw_angle)
            d = (0.4 + 0.4 * alpha / math.pi) * dist
            P1 = (P0s[0] + d * Uout[0], P0s[1] + d * Uout[1])
            P2 = (P3s[0] + d * Uin[0], P3s[1] + d * Uin[1])
            curves.append((P0s, P1, P2, P3s, lab))
        next_port = (port_index[u][lab] + 1) % vertices[u]["deg"]
        traverse(u, next_port)


    def traverse(v, start):
        d = vertices[v]["deg"]
        for off in range(d):
            p = (start + off) % d
            if vertices[v]["cycle"][p] not in visited:
                draw_edge(v, p)
                break


    draw_edge("w1", 0)
    while len(visited) < len(labels):
        for v in list(pos.keys()):
            for idx, lab in enumerate(vertices[v]["cycle"]):
                if lab not in visited:
                    draw_edge(v, idx)

    # ---------- plot ----------
    fig, ax = plt.subplots(figsize=(6, 8))
    rect_w, rect_h = 0.1, 0.24

    # stubs and straight segments
    for p1, p2 in stubs:
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=1.3)
    for p1, p2, lab in straight:
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=1.3)
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax.add_patch(
            Rectangle(
                (mx - rect_w / 2, my - rect_h / 2),
                rect_w,
                rect_h,
                facecolor="white",
                edgecolor="black",
                lw=0.6,
                zorder=5,
            )
        )
        ax.text(mx, my, str(lab), fontsize=9, ha="center", va="center", zorder=6)


    # cubic draw
    def cubic(P0, P1, P2, P3, t):
        u = 1 - t
        return (
            u**3 * P0[0] + 3 * u**2 * t * P1[0] + 3 * u * t**2 * P2[0] + t**3 * P3[0],
            u**3 * P0[1] + 3 * u**2 * t * P1[1] + 3 * u * t**2 * P2[1] + t**3 * P3[1],
        )


    ts = [i / 100 for i in range(101)]
    for P0s, P1, P2, P3s, lab in curves:
        xs = [cubic(P0s, P1, P2, P3s, t)[0] for t in ts]
        ys = [cubic(P0s, P1, P2, P3s, t)[1] for t in ts]
        ax.plot(xs, ys, color="black", lw=1.3)
        mx, my = cubic(P0s, P1, P2, P3s, 0.5)
        ax.add_patch(
            Rectangle(
                (mx - rect_w / 2, my - rect_h / 2),
                rect_w,
                rect_h,
                facecolor="white",
                edgecolor="black",
                lw=0.6,
                zorder=5,
            )
        )
        ax.text(mx, my, str(lab), fontsize=9, ha="center", va="center", zorder=6)
    # vertices
    for v, (x, y) in pos.items():
        face = "white" if v.startswith("w") else "black"
        col = "black" if face == "white" else "white"
        ax.add_patch(
            Circle((x, y), vertex_r, facecolor=face, edgecolor="black", lw=1.5, zorder=8)
        )
        ax.text(x, y, v, fontsize=11, ha="center", va="center", color=col, zorder=9)

    ax.set_aspect("equal")
    ax.axis("off")
    plt.show()


if __name__ == "__main__":
    main()
