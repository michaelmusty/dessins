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
        
        # Plot control points as small blue dots with labels
        logger.info(f"  Drawing control points for label {lab}: P1=({P1[0]:.3f}, {P1[1]:.3f}), P2=({P2[0]:.3f}, {P2[1]:.3f})")
        ax.plot(P1[0], P1[1], 'o', color='blue', markersize=4, zorder=7)
        ax.plot(P2[0], P2[1], 'o', color='blue', markersize=4, zorder=7)
        ax.text(P1[0], P1[1], f'P1_{lab}', fontsize=8, ha='center', va='bottom', color='blue', zorder=7)
        ax.text(P2[0], P2[1], f'P2_{lab}', fontsize=8, ha='center', va='top', color='blue', zorder=7)
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

    # ---------- generate interactive HTML ----------
    logger.info("=== Generating interactive HTML ===")
    
    def generate_html():
        # Build the vertices data
        vertices_data = []
        for v, (x, y) in pos.items():
            face = "white" if v.startswith("w") else "black"
            col = "black" if face == "white" else "white"
            vertices_data.append(f'                {{ id: "{v}", x: {x}, y: {y}, color: "{face}", textColor: "{col}" }}')
        
        # Build the straight edges data - map stub coordinates to vertex coordinates
        straight_edges_data = []
        for p1, p2, lab in straight:
            # Find which vertices this edge connects by looking at the edge mappings
            # We need to map p1 (stub position) to the actual vertex position
            # For now, let's find the closest vertex to p1 and use that as the start
            start_vertex = None
            min_dist = float('inf')
            for v, (vx, vy) in pos.items():
                dist = math.sqrt((p1[0] - vx)**2 + (p1[1] - vy)**2)
                if dist < min_dist:
                    min_dist = dist
                    start_vertex = (vx, vy)
            
            # p2 is already the target vertex position
            mx, my = (start_vertex[0] + p2[0]) / 2, (start_vertex[1] + p2[1]) / 2
            straight_edges_data.append(f'                {{ start: [{start_vertex[0]}, {start_vertex[1]}], end: [{p2[0]}, {p2[1]}], label: "{lab}", labelX: {mx}, labelY: {my} }}')
        
        # Build the curved edges data - map stub coordinates to vertex coordinates
        curved_edges_data = []
        for i, (P0s, P1, P2, P3s, lab) in enumerate(curves):
            # Find the closest vertices to P0s and P3s (the stub endpoints)
            start_vertex = None
            end_vertex = None
            min_dist_start = float('inf')
            min_dist_end = float('inf')
            
            for v, (vx, vy) in pos.items():
                # Check start stub
                dist_start = math.sqrt((P0s[0] - vx)**2 + (P0s[1] - vy)**2)
                if dist_start < min_dist_start:
                    min_dist_start = dist_start
                    start_vertex = (vx, vy)
                
                # Check end stub
                dist_end = math.sqrt((P3s[0] - vx)**2 + (P3s[1] - vy)**2)
                if dist_end < min_dist_end:
                    min_dist_end = dist_end
                    end_vertex = (vx, vy)
            
            mx, my = cubic(P0s, P1, P2, P3s, 0.5)
            curved_edges_data.append(f'                {{ id: {i}, start: [{start_vertex[0]}, {start_vertex[1]}], end: [{end_vertex[0]}, {end_vertex[1]}], control1: [{P1[0]}, {P1[1]}], control2: [{P2[0]}, {P2[1]}], label: "{lab}", labelX: {mx}, labelY: {my} }}')
        
        # Build the control points data
        control_points_data = []
        for i, (P0s, P1, P2, P3s, lab) in enumerate(curves):
            control_points_data.append(f'                {{ id: "P1_{lab}", x: {P1[0]}, y: {P1[1]}, label: "P1_{lab}", edgeId: {i}, control: 1 }}')
            control_points_data.append(f'                {{ id: "P2_{lab}", x: {P2[0]}, y: {P2[1]}, label: "P2_{lab}", edgeId: {i}, control: 2 }}')
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        .container {{ max-width: 1200px; margin: 0 auto; position: relative; }}
        .control-point {{
            cursor: move;
            fill: #007bff;
            stroke: #0056b3;
            stroke-width: 1;
        }}
        .control-point:hover {{ fill: #0056b3; }}
        .control-label {{
            font-size: 10px;
            fill: #007bff;
            font-weight: bold;
            pointer-events: none;
        }}
        .edge {{ stroke: black; stroke-width: 1; fill: none; }}
        .vertex {{ cursor: default; }}
        .vertex-text {{
            font-size: 12px;
            font-weight: bold;
            text-anchor: middle;
            dominant-baseline: middle;
            pointer-events: none;
        }}
        .edge-label {{
            font-size: 14px;
            text-anchor: middle;
            dominant-baseline: middle;
            font-weight: bold;
            pointer-events: none;
        }}
        .edge-label-bg {{
            fill: white;
            stroke: black;
            stroke-width: 1;
            rx: 3;
            ry: 3;
        }}
        .toggle-button {{
            padding: 8px 12px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            z-index: 1000;
            width: 140px;
            white-space: nowrap;
        }}
        .toggle-button:hover {{
            background: #218838;
        }}
        .button-container {{
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            gap: 10px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="button-container">
            <button class="toggle-button" onclick="toggleControlPoints()">Hide Control Points</button>
            <button class="toggle-button" onclick="toggleVertexLabels()">Hide Vertex Labels</button>
            <button class="toggle-button" onclick="toggleEdgeLabels()">Hide Edge Labels</button>
        </div>
        <div id="graph"></div>
    </div>

    <script>
        // Set up the SVG
        const width = 1200;
        const height = 900;
        const margin = 50;

        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("border", "1px solid #ccc")
            .style("background", "white");

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", function(event) {{
                graphGroup.attr("transform", event.transform);
            }});

        svg.call(zoom);
        
        // Create a group for all graph elements
        const graphGroup = svg.append("g");

        // Define the graph data
        const graphData = {{
            vertices: [
{",".join(vertices_data)},
            ],
            straightEdges: [
{",".join(straight_edges_data)},
            ],
            curvedEdges: [
{",".join(curved_edges_data)},
            ]
        }};

        // Calculate the bounds of the graph data
        const allX = [...graphData.vertices.map(v => v.x), ...graphData.straightEdges.flatMap(e => [e.start[0], e.end[0]]), ...graphData.curvedEdges.flatMap(e => [e.start[0], e.end[0], e.control1[0], e.control2[0]])];
        const allY = [...graphData.vertices.map(v => v.y), ...graphData.straightEdges.flatMap(e => [e.start[1], e.end[1]]), ...graphData.curvedEdges.flatMap(e => [e.start[1], e.end[1], e.control1[1], e.control2[1]])];
        
        const minX = Math.min(...allX);
        const maxX = Math.max(...allX);
        const minY = Math.min(...allY);
        const maxY = Math.max(...allY);
        
        // Add some padding around the bounds
        const padding = Math.max(maxX - minX, maxY - minY) * 0.1;
        const xDomain = [minX - padding, maxX + padding];
        const yDomain = [minY - padding, maxY + padding];
        
        // Scale to fit the graph data
        const xScale = d3.scaleLinear()
            .domain(xDomain)
            .range([margin, width - margin]);

        const yScale = d3.scaleLinear()
            .domain(yDomain)
            .range([height - margin, margin]);

        // Create control points data
        const controlPoints = [
{",".join(control_points_data)},
        ];



        // Draw straight edges (first, so they go under vertices)
        graphGroup.selectAll(".straight-edge")
            .data(graphData.straightEdges)
            .enter()
            .append("line")
            .attr("class", "edge")
            .attr("x1", d => xScale(d.start[0]))
            .attr("y1", d => yScale(d.start[1]))
            .attr("x2", d => xScale(d.end[0]))
            .attr("y2", d => yScale(d.end[1]));

        // Draw curved edges (first, so they go under vertices)
        const curvedEdges = graphGroup.selectAll(".curved-edge")
            .data(graphData.curvedEdges)
            .enter()
            .append("path")
            .attr("class", "curved-edge edge")
            .attr("d", d => `M ${{xScale(d.start[0])}} ${{yScale(d.start[1])}} C ${{xScale(d.control1[0])}} ${{yScale(d.control1[1])}} ${{xScale(d.control2[0])}} ${{yScale(d.control2[1])}} ${{xScale(d.end[0])}} ${{yScale(d.end[1])}}`);

        // Draw vertices (after edges, so they appear on top)
        const vertices = graphGroup.selectAll(".vertex")
            .data(graphData.vertices)
            .enter()
            .append("circle")
            .attr("class", "vertex")
            .attr("cx", d => xScale(d.x))
            .attr("cy", d => yScale(d.y))
            .attr("r", 15)
            .attr("fill", d => d.color)
            .attr("stroke", "black")
            .attr("stroke-width", 2);

        // Add vertex labels
        graphGroup.selectAll(".vertex-text")
            .data(graphData.vertices)
            .enter()
            .append("text")
            .attr("class", "vertex-text")
            .attr("x", d => xScale(d.x))
            .attr("y", d => yScale(d.y))
            .attr("fill", d => d.textColor)
            .text(d => d.id);

        // Add straight edge labels with background rectangles
        const straightEdgeLabels = graphGroup.selectAll(".straight-edge-label")
            .data(graphData.straightEdges)
            .enter()
            .append("g")
            .attr("class", "edge-label-group");

        straightEdgeLabels.append("rect")
            .attr("class", "edge-label-bg")
            .attr("x", d => xScale(d.labelX) - 8)
            .attr("y", d => yScale(d.labelY) - 8)
            .attr("width", 16)
            .attr("height", 16);

        straightEdgeLabels.append("text")
            .attr("class", "edge-label")
            .attr("x", d => xScale(d.labelX))
            .attr("y", d => yScale(d.labelY))
            .text(d => d.label);

        // Add curved edge labels with background rectangles
        const curvedEdgeLabels = graphGroup.selectAll(".curved-edge-label")
            .data(graphData.curvedEdges)
            .enter()
            .append("g")
            .attr("class", "edge-label-group");

        curvedEdgeLabels.append("rect")
            .attr("class", "edge-label-bg")
            .attr("x", d => xScale(d.labelX) - 8)
            .attr("y", d => yScale(d.labelY) - 8)
            .attr("width", 16)
            .attr("height", 16);

        curvedEdgeLabels.append("text")
            .attr("class", "edge-label")
            .attr("x", d => xScale(d.labelX))
            .attr("y", d => yScale(d.labelY))
            .text(d => d.label);

        // Draw control points
        const controlPointElements = graphGroup.selectAll(".control-point")
            .data(controlPoints)
            .enter()
            .append("circle")
            .attr("class", "control-point")
            .attr("cx", d => xScale(d.x))
            .attr("cy", d => yScale(d.y))
            .attr("r", 6);

        // Add control point labels
        graphGroup.selectAll(".control-label")
            .data(controlPoints)
            .enter()
            .append("text")
            .attr("class", "control-label")
            .attr("id", d => d.id)
            .attr("x", d => xScale(d.x))
            .attr("y", d => yScale(d.y) - 10)
            .text(d => d.label);

        // Function to update curved edge
        function updateCurvedEdge(edgeId) {{
            // Find the edge and its control points
            const edge = graphData.curvedEdges.find(e => e.id === edgeId);
            const cp1 = controlPoints.find(cp => cp.edgeId === edgeId && cp.control === 1);
            const cp2 = controlPoints.find(cp => cp.edgeId === edgeId && cp.control === 2);

            // Update the control points in the edge data
            edge.control1 = [cp1.x, cp1.y];
            edge.control2 = [cp2.x, cp2.y];

            // Update the path for this edge
            graphGroup.selectAll(".curved-edge")
                .filter(d => d.id === edgeId)
                .attr("d", d => `M ${{xScale(d.start[0])}} ${{yScale(d.start[1])}} C ${{xScale(edge.control1[0])}} ${{yScale(edge.control1[1])}} ${{xScale(edge.control2[0])}} ${{yScale(edge.control2[1])}} ${{xScale(d.end[0])}} ${{yScale(d.end[1])}}`);
            
            // Update the edge label position
            // Calculate a point on the curve at t=0.5 (middle of the curve)
            const t = 0.5;
            const x = Math.pow(1-t, 3) * edge.start[0] + 
                      3 * Math.pow(1-t, 2) * t * edge.control1[0] + 
                      3 * (1-t) * Math.pow(t, 2) * edge.control2[0] + 
                      Math.pow(t, 3) * edge.end[0];
            const y = Math.pow(1-t, 3) * edge.start[1] + 
                      3 * Math.pow(1-t, 2) * t * edge.control1[1] + 
                      3 * (1-t) * Math.pow(t, 2) * edge.control2[1] + 
                      Math.pow(t, 3) * edge.end[1];
            
            // Update the label position and background rectangle
            graphGroup.selectAll(".edge-label-group")
                .filter(d => d.id === edgeId)
                .select("rect")
                .attr("x", xScale(x) - 8)
                .attr("y", yScale(y) - 8);

            graphGroup.selectAll(".edge-label-group")
                .filter(d => d.id === edgeId)
                .select("text")
                .attr("x", xScale(x))
                .attr("y", yScale(y));
        }}

        // Drag behavior for control points
        const drag = d3.drag()
            .on("start", function(event, d) {{
                // Store initial positions
                d.startX = d.x;
                d.startY = d.y;
                d.startEventX = event.x;
                d.startEventY = event.y;
            }})
            .on("drag", function(event, d) {{
                // Calculate the change in event coordinates
                const deltaX = event.x - d.startEventX;
                const deltaY = event.y - d.startEventY;
                
                // Convert delta to data coordinates using the scale
                const deltaDataX = xScale.invert(d.startEventX + deltaX) - xScale.invert(d.startEventX);
                const deltaDataY = yScale.invert(d.startEventY + deltaY) - yScale.invert(d.startEventY);
                
                // Update control point data (no boundary constraints)
                d.x = d.startX + deltaDataX;
                d.y = d.startY + deltaDataY;
                
                // Update visual position using the scale
                const newSvgX = xScale(d.x);
                const newSvgY = yScale(d.y);
                
                d3.select(this)
                    .attr("cx", newSvgX)
                    .attr("cy", newSvgY);

                // Update label position
                graphGroup.selectAll(".control-label")
                    .filter(label => label.id === d.id)
                    .attr("x", newSvgX)
                    .attr("y", newSvgY - 10);

                // Update the curve
                updateCurvedEdge(d.edgeId);
            }});

        // Apply drag behavior to control points
        controlPointElements.call(drag);

        // Toggle control points visibility
        window.toggleControlPoints = function() {{
            const button = document.querySelector('.toggle-button');
            const controlPoints = document.querySelectorAll('.control-point, .control-label');
            const isVisible = controlPoints[0].style.display !== 'none';
            
            controlPoints.forEach(point => {{
                point.style.display = isVisible ? 'none' : 'block';
            }});
            
            button.textContent = isVisible ? 'Show Control Points' : 'Hide Control Points';
        }};

        // Toggle vertex labels visibility
        window.toggleVertexLabels = function() {{
            const button = document.querySelectorAll('.toggle-button')[1];
            const vertexLabels = document.querySelectorAll('.vertex-text');
            const isVisible = vertexLabels[0].style.display !== 'none';
            
            vertexLabels.forEach(label => {{
                label.style.display = isVisible ? 'none' : 'block';
            }});
            
            button.textContent = isVisible ? 'Show Vertex Labels' : 'Hide Vertex Labels';
        }};

        // Toggle edge labels visibility
        window.toggleEdgeLabels = function() {{
            const button = document.querySelectorAll('.toggle-button')[2];
            const edgeLabels = document.querySelectorAll('.edge-label-group');
            const isVisible = edgeLabels[0].style.display !== 'none';
            
            edgeLabels.forEach(label => {{
                label.style.display = isVisible ? 'none' : 'block';
            }});
            
            button.textContent = isVisible ? 'Show Edge Labels' : 'Hide Edge Labels';
        }};
    </script>
</body>
</html>"""
        
        return html_content
    
    # Generate and save HTML file
    html_content = generate_html()
    
    # Create a descriptive filename based on the permutations
    white_clean = args.white.replace("(", "").replace(")", "").replace(",", "_").replace(" ", "")
    black_clean = args.black.replace("(", "").replace(")", "").replace(",", "_").replace(" ", "")
    html_filename = f"everett_{white_clean}_vs_{black_clean}.html"
    
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Interactive HTML saved to {html_filename}")


if __name__ == "__main__":
    main()
