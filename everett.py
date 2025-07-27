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
from loguru import logger

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)


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
    logger.info(f"Parsing white permutation: {sigma0}")
    logger.info(f"Parsing black permutation: {sigma1}")
    
    cw = parse_cycles(sigma0)
    cb = parse_cycles(sigma1)
    logger.info(f"White cycles: {cw}")
    logger.info(f"Black cycles: {cb}")
    
    labels = {label for c in cw + cb for label in c}
    logger.info(f"All labels: {sorted(labels)}")
    
    ensure_singletons(cw, labels)
    ensure_singletons(cb, labels)
    cw.sort(key=min)
    cb.sort(key=min)
    cw[0] = rotate_cycle(cw[0], 1)
    logger.info(f"Final white cycles: {cw}")
    logger.info(f"Final black cycles: {cb}")

    vertices = {}
    wmap, bmap = {}, {}
    logger.info("Creating white vertices:")
    for idx, cyc in enumerate(cw, 1):
        vid = f"w{idx}"
        vertices[vid] = {"cycle": cyc, "deg": len(cyc), "color": "white"}
        logger.info(f"  Created vertex {vid} with cycle {cyc} (degree {len(cyc)})")
        for label in cyc:
            wmap[label] = vid
            logger.info(f"    Label {label} maps to vertex {vid}")
    
    logger.info("Creating black vertices:")
    for idx, cyc in enumerate(cb, 1):
        vid = f"b{idx}"
        vertices[vid] = {"cycle": cyc, "deg": len(cyc), "color": "black"}
        logger.info(f"  Created vertex {vid} with cycle {cyc} (degree {len(cyc)})")
        for label in cyc:
            bmap[label] = vid
            logger.info(f"    Label {label} maps to vertex {vid}")

    edges = {label: {"white": wmap[label], "black": bmap[label]} for label in labels}
    logger.info("Edge mappings:")
    for label, mapping in edges.items():
        logger.info(f"  Label {label}: white vertex {mapping['white']} -> black vertex {mapping['black']}")


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
        logger.info(f"Placed vertex {v_new} at position ({pos[v_new][0]:.3f}, {pos[v_new][1]:.3f}) from origin ({origin[0]:.3f}, {origin[1]:.3f}) in direction {math.degrees(dir_angle):.1f}°")
        logger.info(f"  Vertex {v_new} connects to label {lab} at port {k} with orientation {math.degrees(orient[v_new]):.1f}°")


    def draw_edge(v, pidx):
        lab = vertices[v]["cycle"][pidx]
        if lab in visited:
            logger.info(f"Edge for label {lab} already visited, skipping")
            return
        
        logger.info(f"=== Drawing edge for label {lab} ===")
        logger.info(f"Starting from vertex {v} at port {pidx}")
        
        visited.add(lab)
        w, b = edges[lab]["white"], edges[lab]["black"]
        u = b if v == w else w
        logger.info(f"Edge connects {v} (port {pidx}) to {u}")
        logger.info(f"White vertex: {w}, Black vertex: {b}")
        
        theta_out = orient[v] + port_angle(v, pidx)
        P0 = pos[v]
        Uout = unit(theta_out)
        P0s = (P0[0] + stub_len * Uout[0], P0[1] + stub_len * Uout[1])
        stubs.append((P0, P0s))
        logger.info(f"Starting point: ({P0[0]:.3f}, {P0[1]:.3f}), direction: {math.degrees(theta_out):.1f}°")
        logger.info(f"Stub endpoint: ({P0s[0]:.3f}, {P0s[1]:.3f})")
        
        if u not in pos:
            logger.info(f"Target vertex {u} not yet placed, creating new vertex")
            place_vertex(u, P0, theta_out, lab)
            straight.append((P0s, pos[u], lab))
            logger.info(f"Added straight edge from ({P0s[0]:.3f}, {P0s[1]:.3f}) to ({pos[u][0]:.3f}, {pos[u][1]:.3f})")
        else:
            logger.info(f"Target vertex {u} already exists at ({pos[u][0]:.3f}, {pos[u][1]:.3f})")
            kin = port_index[u][lab]
            theta_u_out = orient[u] + port_angle(u, kin)  # outgoing direction at u
            Uin = unit(theta_u_out)
            Pin = pos[u]
            P3s = (Pin[0] + stub_len * Uin[0], Pin[1] + stub_len * Uin[1])
            stubs.append((Pin, P3s))
            logger.info(f"Target direction: {math.degrees(theta_u_out):.1f}°, stub endpoint: ({P3s[0]:.3f}, {P3s[1]:.3f})")
            
            dist = math.dist(P0s, P3s)
            # angle differences for scaling d
            cw_angle = (theta_out - theta_u_out) % (2 * math.pi)
            ccw_angle = (theta_u_out - theta_out) % (2 * math.pi)
            alpha = min(cw_angle, ccw_angle)
            d = (0.4 + 0.4 * alpha / math.pi) * dist
            P1 = (P0s[0] + d * Uout[0], P0s[1] + d * Uout[1])
            P2 = (P3s[0] + d * Uin[0], P3s[1] + d * Uin[1])
            curves.append((P0s, P1, P2, P3s, lab))
            
            # Determine curve wrapping direction
            if cw_angle < ccw_angle:
                wrap_direction = "clockwise"
            else:
                wrap_direction = "counterclockwise"
            
            logger.info(f"Distance between stubs: {dist:.3f}")
            logger.info(f"Angle difference: {math.degrees(alpha):.1f}°")
            logger.info(f"Curve wraps {wrap_direction} from {v} to {u}")
            logger.info(f"Control points: P1=({P1[0]:.3f}, {P1[1]:.3f}), P2=({P2[0]:.3f}, {P2[1]:.3f})")
            logger.info("Added curved edge with control points")
        
        next_port = (port_index[u][lab] + 1) % vertices[u]["deg"]
        logger.info(f"Next traversal: vertex {u}, port {next_port}")
        # Note: Face traversal is now handled in the main loop


    def traverse(v, start):
        d = vertices[v]["deg"]
        logger.info(f"Traversing vertex {v} (degree {d}) starting from port {start}")
        for off in range(d):
            p = (start + off) % d
            lab = vertices[v]["cycle"][p]
            logger.info(f"  Checking port {p} with label {lab} (visited: {lab in visited})")
            if lab not in visited:
                logger.info(f"  Found unvisited label {lab}, drawing edge")
                draw_edge(v, p)
                return True  # Found and drew an edge, continue face traversal
        logger.info(f"  All ports at vertex {v} already visited")
        return False  # No unvisited edges found at this vertex


    logger.info("=== Starting edge drawing process ===")
    logger.info(f"Total labels to process: {len(labels)}")
    
    # Start with the first edge and continue face traversal
    current_vertex = "w1"
    current_port = 0
    
    iteration = 1
    while len(visited) < len(labels):
        logger.info(f"=== Iteration {iteration} ===")
        logger.info(f"Current visited labels: {len(visited)}/{len(labels)}")
        logger.info(f"Placed vertices: {list(pos.keys())}")
        
        # If this is the first iteration, start with the first edge
        if iteration == 1:
            start_vertex = current_vertex
            start_port = current_port
            logger.info(f"Starting first face traversal from vertex {start_vertex}, port {start_port}")
        else:
            # Find a vertex with unvisited edges to start a new face
            start_vertex = None
            start_port = None
            for v in list(pos.keys()):
                for idx, lab in enumerate(vertices[v]["cycle"]):
                    if lab not in visited:
                        start_vertex = v
                        start_port = idx
                        logger.info(f"Starting new face traversal from vertex {v}, port {idx} (label {lab})")
                        break
                if start_vertex:
                    break
        
        if not start_vertex:
            logger.warning("No unvisited edges found!")
            break
        
        # Traverse the face starting from this vertex/port
        current_vertex = start_vertex
        current_port = start_port
        
        # Keep track of the path we've taken for backtracking
        path = []
        
        while True:
            logger.info(f"Face traversal: drawing edge from {current_vertex}, port {current_port}")
            draw_edge(current_vertex, current_port)
            
            # Record this step in our path
            path.append((current_vertex, current_port))
            
            # Find the next vertex and port by following the edge
            lab = vertices[current_vertex]["cycle"][current_port]
            next_vertex = edges[lab]["black"] if current_vertex.startswith("w") else edges[lab]["white"]
            next_port = port_index[next_vertex][lab]
            
            logger.info(f"Face traversal: following edge to {next_vertex}, port {next_port}")
            
            # Check if the next vertex has unvisited edges by moving counterclockwise
            found_unvisited = False
            for off in range(vertices[next_vertex]["deg"]):
                p = (next_port + off) % vertices[next_vertex]["deg"]
                if vertices[next_vertex]["cycle"][p] not in visited:
                    current_vertex = next_vertex
                    current_port = p
                    found_unvisited = True
                    logger.info(f"Found unvisited edge at vertex {next_vertex}, port {p}")
                    break
            
            if not found_unvisited:
                # No unvisited edges at next vertex, backtrack to the vertex we came from
                if len(path) > 0:
                    # Go back to the vertex we just came from and continue counterclockwise
                    prev_vertex, prev_port = path[-1]  # Get the vertex we just came from
                    current_vertex = prev_vertex
                    current_port = (prev_port + 1) % vertices[prev_vertex]["deg"]
                    logger.info(f"Backtracking to {current_vertex}, port {current_port}")
                    
                    # Check if this port has an unvisited edge
                    lab = vertices[current_vertex]["cycle"][current_port]
                    if lab not in visited:
                        logger.info(f"Found unvisited edge after backtracking")
                        continue
                    else:
                        logger.info(f"Face traversal complete after backtracking")
                        break
                else:
                    logger.info(f"Face traversal complete - no more backtracking possible")
                    break
        
        iteration += 1
    
    logger.info("=== Edge drawing complete ===")
    logger.info(f"Final visited labels: {len(visited)}/{len(labels)}")
    logger.info(f"Total vertices placed: {len(pos)}")
    logger.info(f"Total stubs: {len(stubs)}")
    logger.info(f"Total straight edges: {len(straight)}")
    logger.info(f"Total curved edges: {len(curves)}")

    # ---------- plot ----------
    logger.info("=== Starting plot generation ===")
    fig, ax = plt.subplots(figsize=(6, 8))
    rect_w, rect_h = 0.1, 0.24

    # stubs and straight segments
    logger.info(f"Drawing {len(stubs)} stubs")
    for p1, p2 in stubs:
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=1.3)
    
    logger.info(f"Drawing {len(straight)} straight edges")
    for p1, p2, lab in straight:
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=1.3)
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        logger.info(f"  Drawing straight edge for label {lab} from ({p1[0]:.3f}, {p1[1]:.3f}) to ({p2[0]:.3f}, {p2[1]:.3f})")
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


    logger.info(f"Drawing {len(curves)} curved edges")
    ts = [i / 100 for i in range(101)]
    for P0s, P1, P2, P3s, lab in curves:
        xs = [cubic(P0s, P1, P2, P3s, t)[0] for t in ts]
        ys = [cubic(P0s, P1, P2, P3s, t)[1] for t in ts]
        ax.plot(xs, ys, color="black", lw=1.3)
        mx, my = cubic(P0s, P1, P2, P3s, 0.5)
        logger.info(f"  Drawing curved edge for label {lab} from ({P0s[0]:.3f}, {P0s[1]:.3f}) to ({P3s[0]:.3f}, {P3s[1]:.3f})")
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
    logger.info(f"Drawing {len(pos)} vertices")
    for v, (x, y) in pos.items():
        face = "white" if v.startswith("w") else "black"
        col = "black" if face == "white" else "white"
        logger.info(f"  Drawing vertex {v} at position ({x:.3f}, {y:.3f}) with color {face}")
        ax.add_patch(
            Circle((x, y), vertex_r, facecolor=face, edgecolor="black", lw=1.5, zorder=8)
        )
        ax.text(x, y, v, fontsize=11, ha="center", va="center", color=col, zorder=9)

    ax.set_aspect("equal")
    ax.axis("off")
    logger.info("Saving plot to temp.png")
    plt.savefig("temp.png", dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
