"""
Generate interactive Everett diagrams from LMFDB Belyi map data

This script processes LMFDB galmap data and generates interactive HTML diagrams
organized by passport structure.

Example usage:
    python generate_dessin.py --galmap "7T6-4.2.1_3.2.2_3.2.2-a"
    python generate_dessin.py --passport "7T6-4.2.1_3.2.2_3.2.2"
    python generate_dessin.py --all
"""

import argparse
import math
import re
import os
import json
from pathlib import Path
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

# Use actual LMFDB lite interface
from lmf import db

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


def get_lmfdb_galmap(galmap_label):
    """Get galmap data from LMFDB using lmfdb_lite"""
    galmaps = list(db.belyi_galmaps.search({"label": galmap_label}))
    if galmaps:
        return galmaps[0]
    return None


def get_lmfdb_passport(passport_label):
    """Get passport data from LMFDB using lmfdb_lite"""
    passports = list(db.belyi_passports.search({"plabel": passport_label}))
    if passports:
        return passports[0]
    return None


def get_galmaps_by_passport(passport_label):
    """Get all galmaps for a given passport using lmfdb_lite"""
    galmaps = list(db.belyi_galmaps.search({"plabel": passport_label}))
    return galmaps


def create_directory_structure():
    """Create the directory structure for organizing diagrams"""
    dirs = [
        "passports",
        "galmaps", 
        "diagrams"
    ]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)


def generate_galmap_page(galmap_label):
    """Generate an HTML page for a single galmap showing all its diagrams"""
    galmap_data = get_lmfdb_galmap(galmap_label)
    if not galmap_data:
        logger.error(f"Galmap {galmap_label} not found")
        return
    
    passport_label = galmap_data["plabel"]
    triples_cyc = galmap_data["triples_cyc"]
    
    logger.info(f"Generating galmap page for {galmap_label}")
    logger.info(f"Found {len(triples_cyc)} triples")
    
    # Create directory structure
    galmap_dir = Path("galmaps") / galmap_label
    galmap_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate individual diagram files
    diagram_files = []
    for i, triple in enumerate(triples_cyc):
        if len(triple) >= 3:  # Need all three permutations (σ₀, σ₁, σ∞)
            sigma0 = triple[0]
            sigma1 = triple[1]
            sigma_inf = triple[2]
            
            # Generate the diagram
            diagram_filename = f"diagram_{i+1}.html"
            diagram_path = galmap_dir / diagram_filename
            
            try:
                generate_single_diagram(sigma0, sigma1, diagram_path, galmap_label, passport_label, i)
                diagram_files.append({
                    "filename": diagram_filename,
                    "sigma0": sigma0,
                    "sigma1": sigma1,
                    "sigma_inf": sigma_inf,
                    "index": i+1
                })
                logger.info(f"Generated diagram {i+1}: σ₀ = {sigma0}, σ₁ = {sigma1}, σ∞ = {sigma_inf}")
            except Exception as e:
                logger.error(f"Failed to generate diagram {i+1}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Generate the galmap index page
    generate_galmap_index(galmap_data, diagram_files, galmap_dir)
    
    return galmap_dir


def generate_single_diagram(white_perm, black_perm, output_path, galmap_label, passport_label, embedding_index=None):
    """Generate a single diagram from permutation strings"""
    # Parse permutations
    cw = parse_cycles(white_perm)
    cb = parse_cycles(black_perm)
    
    labels = {label for c in cw + cb for label in c}
    ensure_singletons(cw, labels)
    ensure_singletons(cb, labels)
    cw.sort(key=min)
    cb.sort(key=min)
    if cw:
        cw[0] = rotate_cycle(cw[0], 1)
    
    # Generate the diagram (reuse existing logic)
    vertices = {}
    wmap, bmap = {}, {}
    
    # Create white vertices
    for idx, cyc in enumerate(cw, 1):
        vid = f"w{idx}"
        vertices[vid] = {"cycle": cyc, "deg": len(cyc), "color": "white"}
        for label in cyc:
            wmap[label] = vid
    
    # Create black vertices  
    for idx, cyc in enumerate(cb, 1):
        vid = f"b{idx}"
        vertices[vid] = {"cycle": cyc, "deg": len(cyc), "color": "black"}
        for label in cyc:
            bmap[label] = vid

    edges = {label: {"white": wmap[label], "black": bmap[label]} for label in labels}
    
    # Generate the diagram layout (simplified version of the original logic)
    L = 1.4
    vertex_r = 0.22
    stub_len = vertex_r
    pos = {"w1": (0, 0)}
    orient = {"w1": 0.0}
    visited = set()
    straight = []
    curves = []
    stubs = []
    
    # Initialize all vertices in orient dictionary
    for v in vertices.keys():
        if v not in orient:
            orient[v] = 0.0

    def port_angle(v, idx):
        return idx * 2 * math.pi / vertices[v]["deg"]

    port_index = {
        v: {lab: i for i, lab in enumerate(vertices[v]["cycle"])} for v in vertices
    }

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
            theta_u_out = orient[u] + port_angle(u, kin)
            Uin = unit(theta_u_out)
            Pin = pos[u]
            P3s = (Pin[0] + stub_len * Uin[0], Pin[1] + stub_len * Uin[1])
            stubs.append((Pin, P3s))
            
            dist = math.dist(P0s, P3s)
            cw_angle = (theta_out - theta_u_out) % (2 * math.pi)
            ccw_angle = (theta_u_out - theta_out) % (2 * math.pi)
            alpha = min(cw_angle, ccw_angle)
            d = (0.4 + 0.4 * alpha / math.pi) * dist
            P1 = (P0s[0] + d * Uout[0], P0s[1] + d * Uout[1])
            P2 = (P3s[0] + d * Uin[0], P3s[1] + d * Uin[1])
            curves.append((P0s, P1, P2, P3s, lab))

    # Use the original edge traversal logic from everett.py
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

    # Calculate the third permutation (σ∞) from σ₀ and σ₁
    # σ₀ * σ₁ * σ∞ = identity, so σ∞ = (σ₀ * σ₁)^(-1)
    def multiply_permutations(perm1, perm2):
        """Multiply two permutations in cycle notation"""
        # Convert to mapping representation
        n = max(max(int(x) for x in str(perm1).replace('(', '').replace(')', '').split(',') if x.strip().isdigit()),
                max(int(x) for x in str(perm2).replace('(', '').replace(')', '').split(',') if x.strip().isdigit()))
        
        # Create mapping for perm1
        mapping1 = {}
        for cycle in perm1.strip('()').split(')('):
            cycle = cycle.strip('()')
            if cycle:
                nums = [int(x.strip()) for x in cycle.split(',')]
                for i in range(len(nums)):
                    mapping1[nums[i]] = nums[(i + 1) % len(nums)]
        
        # Create mapping for perm2
        mapping2 = {}
        for cycle in perm2.strip('()').split(')('):
            cycle = cycle.strip('()')
            if cycle:
                nums = [int(x.strip()) for x in cycle.split(',')]
                for i in range(len(nums)):
                    mapping2[nums[i]] = nums[(i + 1) % len(nums)]
        
        # Multiply permutations: (perm1 * perm2)(i) = perm1(perm2(i))
        result_mapping = {}
        for i in range(1, n + 1):
            result_mapping[i] = mapping1.get(mapping2.get(i, i), mapping2.get(i, i))
        
        # Convert back to cycle notation
        visited = set()
        cycles = []
        for i in range(1, n + 1):
            if i not in visited:
                cycle = []
                j = i
                while j not in visited:
                    visited.add(j)
                    cycle.append(j)
                    j = result_mapping.get(j, j)
                if len(cycle) > 1:
                    cycles.append('(' + ','.join(map(str, cycle)) + ')')
        
        return ''.join(cycles) if cycles else '(1)'
    
    def inverse_permutation(perm):
        """Calculate the inverse of a permutation"""
        # For a cycle (a,b,c), the inverse is (c,b,a)
        if perm == '(1)':
            return '(1)'
        
        result = []
        for cycle in perm.strip('()').split(')('):
            cycle = cycle.strip('()')
            if cycle:
                nums = [int(x.strip()) for x in cycle.split(',')]
                result.append('(' + ','.join(map(str, reversed(nums))) + ')')
        
        return ''.join(result)
    
    # Calculate σ∞ = (σ₀ * σ₁)^(-1)
    product = multiply_permutations(white_perm, black_perm)
    sigma_inf = inverse_permutation(product)
    
    # Get galmap data for base field and embeddings
    galmap_data = get_lmfdb_galmap(galmap_label)
    base_field = galmap_data.get('base_field') if galmap_data else None
    embeddings = galmap_data.get('embeddings') if galmap_data else None
    
    # Generate HTML
    html_content = generate_interactive_html(pos, straight, curves, stubs, white_perm, black_perm, sigma_inf, galmap_label, passport_label, base_field, embeddings, embedding_index)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def generate_interactive_html(pos, straight, curves, stubs, white_perm, black_perm, sigma_inf, galmap_label, passport_label, base_field=None, embeddings=None, embedding_index=None):
    """Generate the interactive HTML content (simplified version)"""
    
    def format_minimal_polynomial(coeffs):
        """Format minimal polynomial coefficients as a readable polynomial"""
        if not coeffs:
            return "Q"
        
        # Reverse coefficients so that coeffs[0] is the constant term
        coeffs = list(reversed(coeffs))
        
        terms = []
        for i, coeff in enumerate(coeffs):
            if coeff == 0:
                continue
            if i == 0:
                terms.append(str(coeff))
            elif i == 1:
                if coeff == 1:
                    terms.append("T")
                elif coeff == -1:
                    terms.append("-T")
                else:
                    terms.append(f"{coeff}T")
            else:
                if coeff == 1:
                    terms.append(f"T^{i}")
                elif coeff == -1:
                    terms.append(f"-T^{i}")
                else:
                    terms.append(f"{coeff}T^{i}")
        
        if not terms:
            return "0"
        
        # Join terms with + signs, but handle negative coefficients
        result = terms[0]
        for term in terms[1:]:
            if term.startswith('-'):
                result += f" - {term[1:]}"
            else:
                result += f" + {term}"
        
        return result
    
    def format_embedding(embedding):
        """Format embedding as a complex number"""
        if len(embedding) == 2:
            real, imag = embedding
            if abs(imag) < 1e-10:
                return f"{real:.6f}"
            elif abs(real) < 1e-10:
                if abs(imag - 1) < 1e-10:
                    return "√(-1)"
                elif abs(imag + 1) < 1e-10:
                    return "-√(-1)"
                else:
                    return f"{imag:.6f}√(-1)"
            else:
                if imag > 0:
                    return f"{real:.6f} + {imag:.6f}√(-1)"
                else:
                    return f"{real:.6f} - {abs(imag):.6f}√(-1)"
        return str(embedding)
    
    # Build vertices data
    vertices_data = []
    for v, (x, y) in pos.items():
        face = "white" if v.startswith("w") else "black"
        col = "black" if face == "white" else "white"
        vertices_data.append(f'                {{ id: "{v}", x: {x}, y: {y}, color: "{face}", textColor: "{col}" }}')
    
    # Build straight edges data - map stub coordinates to vertex coordinates
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
    
    # Build curved edges data - map stub coordinates to vertex coordinates
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
        
        # Calculate a point on the curve at t=0.5 (middle of the curve) using cubic Bezier formula
        t = 0.5
        mx = (1-t)**3 * start_vertex[0] + 3*(1-t)**2*t * P1[0] + 3*(1-t)*t**2 * P2[0] + t**3 * end_vertex[0]
        my = (1-t)**3 * start_vertex[1] + 3*(1-t)**2*t * P1[1] + 3*(1-t)*t**2 * P2[1] + t**3 * end_vertex[1]
        
        curved_edges_data.append(f'                {{ id: {i}, start: [{start_vertex[0]}, {start_vertex[1]}], end: [{end_vertex[0]}, {end_vertex[1]}], control1: [{P1[0]}, {P1[1]}], control2: [{P2[0]}, {P2[1]}], label: "{lab}", labelX: {mx}, labelY: {my} }}')
    
    # Build the control points data
    control_points_data = []
    for i, (P0s, P1, P2, P3s, lab) in enumerate(curves):
        control_points_data.append(f'                {{ id: "P1_{lab}", x: {P1[0]}, y: {P1[1]}, label: "P1_{lab}", edgeId: {i}, control: 1 }}')
        control_points_data.append(f'                {{ id: "P2_{lab}", x: {P2[0]}, y: {P2[1]}, label: "P2_{lab}", edgeId: {i}, control: 2 }}')

    # Enhanced HTML template with minimal layout and navigation
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dessin: σ₀ = {white_perm}, σ₁ = {black_perm}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        .nav {{
            background: #f8f9fa;
            padding: 10px 20px;
            border-bottom: 1px solid #dee2e6;
            font-size: 14px;
        }}
        .nav a {{
            color: #007bff;
            text-decoration: none;
            margin-right: 20px;
        }}
        .nav a:hover {{
            text-decoration: underline;
        }}
        .container {{ width: 100%; height: calc(100vh - 50px); position: relative; }}
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
    <div class="nav">
        <a href="index.html">← Back to Galmap</a>
        <a href="../../passports/{passport_label}/index.html">← Back to Passport</a>
        <a href="https://beta.lmfdb.org/Belyi/{galmap_label}" target="_blank">View on LMFDB</a>
        <span style="margin-left: 20px; font-weight: bold;">σ₀ = {white_perm}, σ₁ = {black_perm}, σ∞ = {sigma_inf}</span>
        {f'<span style="margin-left: 20px;">Base field: {format_minimal_polynomial(base_field)}</span>' if base_field else ''}
        {f'<span style="margin-left: 20px;">Embedding: {format_embedding(embeddings[embedding_index])}</span>' if embeddings and embedding_index is not None and embedding_index < len(embeddings) else ''}
    </div>
    <div class="container">
        <div class="button-container">
            <button class="toggle-button" onclick="toggleControlPoints()">Hide Control Points</button>
            <button class="toggle-button" onclick="toggleVertexLabels()">Hide Vertex Labels</button>
            <button class="toggle-button" onclick="toggleEdgeLabels()">Hide Edge Labels</button>
            <button class="toggle-button" onclick="captureScreen()">Screen Capture</button>
        </div>
        <div id="graph"></div>
    </div>

    <script>
        // Set up the SVG - use full container size
        const width = window.innerWidth;
        const height = window.innerHeight - 50; // Account for nav bar
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
{",".join(straight_edges_data) if straight_edges_data else ""},
            ],
            curvedEdges: [
{",".join(curved_edges_data) if curved_edges_data else ""},
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
{",".join(control_points_data) if control_points_data else ""},
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
        
        // Screen capture function
        function captureScreen() {{
            // Create filename with LMFDB label and permutation triple
            const filename = '{galmap_label}_σ₀={white_perm}_σ₁={black_perm}_σ∞={sigma_inf}.png';
            
            // Create a custom canvas for the image
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Set canvas size (2400x1600 for high resolution)
            canvas.width = 2400;
            canvas.height = 1600;
            
            // Fill with white background
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Add metadata at the top
            ctx.fillStyle = 'black';
            ctx.font = 'bold 48px Arial'; // Doubled font size for higher resolution
            ctx.textAlign = 'left';
            
            let yPos = 80; // Doubled starting position
            const lineHeight = 70; // Doubled line height
            
            // Add permutation triple
            ctx.fillText(`σ₀ = {white_perm}, σ₁ = {black_perm}, σ∞ = {sigma_inf}`, 40, yPos);
            yPos += lineHeight;
            
            // Add base field if available
            {f'ctx.fillText(`Base field: {format_minimal_polynomial(base_field)}`, 40, yPos); yPos += lineHeight;' if base_field else ''}
            
            // Add embedding if available
            {f'ctx.fillText(`Embedding: {format_embedding(embeddings[embedding_index])}`, 40, yPos); yPos += lineHeight;' if embeddings and embedding_index is not None and embedding_index < len(embeddings) else ''}
            
            // Capture the SVG element
            html2canvas(document.querySelector('#graph'), {{
                backgroundColor: 'white',
                scale: 4, // Increased scale for higher quality
                useCORS: true,
                allowTaint: true,
                logging: false,
                imageTimeout: 0,
                removeContainer: true
            }}).then(svgCanvas => {{
                // Calculate dimensions to fit the dessin in the remaining space
                const dessinHeight = canvas.height - yPos - 40; // Leave some padding
                const dessinWidth = canvas.width - 80; // Leave padding on sides
                
                // Calculate scaling to fit the dessin
                const scaleX = dessinWidth / svgCanvas.width;
                const scaleY = dessinHeight / svgCanvas.height;
                const scale = Math.min(scaleX, scaleY);
                
                // Calculate centered position
                const scaledWidth = svgCanvas.width * scale;
                const scaledHeight = svgCanvas.height * scale;
                const x = (canvas.width - scaledWidth) / 2;
                const y = yPos + 20;
                
                // Draw the dessin
                ctx.drawImage(svgCanvas, x, y, scaledWidth, scaledHeight);
                
                // Create download link
                const link = document.createElement('a');
                link.download = filename;
                link.href = canvas.toDataURL('image/png');
                link.click();
            }});
        }};
    </script>
</body>
</html>"""
    
    return html_content


def generate_galmap_index(galmap_data, diagram_files, galmap_dir):
    """Generate an index page for a galmap showing all its diagrams"""
    galmap_label = galmap_data["label"]
    passport_label = galmap_data["plabel"]
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Galmap: {galmap_label}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .diagram-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 20px; }}
        .diagram-item {{ border: 1px solid #ccc; padding: 10px; text-align: center; }}
        .diagram-item iframe {{ width: 100%; height: 500px; border: none; }}
        .metadata {{ background: #f5f5f5; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
        .nav {{ margin-bottom: 20px; }}
        .nav a {{ margin-right: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/dessins/passports/{passport_label}/index.html">← Back to Passport Index</a>
            <a href="/dessins/index.html">← Back to Main Index</a>
        </div>
        
        <h1>Galmap: {galmap_label}</h1>
        
        <div class="metadata">
            <h3>Galmap Metadata</h3>
            <p><strong>Passport:</strong> {passport_label}</p>
            <p><strong>Degree:</strong> {galmap_data.get('deg', 'N/A')}</p>
            <p><strong>Group:</strong> {galmap_data.get('group', 'N/A')}</p>
            <p><strong>Genus:</strong> {galmap_data.get('g', 'N/A')}</p>
            <p><strong>Geometric Type:</strong> {galmap_data.get('geomtype', 'N/A')}</p>
            <p><strong>Orbit Size:</strong> {galmap_data.get('orbit_size', 'N/A')}</p>
            <p><strong>LMFDB:</strong> <a href="https://beta.lmfdb.org/Belyi/{galmap_data.get('label', galmap_label)}" target="_blank">View on LMFDB</a></p>
        </div>
        
        <h2>Dessins ({len(diagram_files)})</h2>
        <div class="diagram-grid">
"""
    
    for diagram in diagram_files:
        html_content += f"""
            <div class="diagram-item">
                <h3><a href="{diagram['filename']}">Dessin {diagram['index']}</a></h3>
                <p>σ₀ = {diagram['sigma0']}, σ₁ = {diagram['sigma1']}, σ∞ = {diagram['sigma_inf']}</p>
            </div>
"""
    
    html_content += """
        </div>
    </div>
</body>
</html>"""
    
    with open(galmap_dir / "index.html", 'w', encoding='utf-8') as f:
        f.write(html_content)


def generate_passport_page(passport_label):
    """Generate an HTML page for a passport showing all its galmaps"""
    passport_data = get_lmfdb_passport(passport_label)
    if not passport_data:
        logger.error(f"Passport {passport_label} not found")
        return None
    
    galmaps = get_galmaps_by_passport(passport_label)
    logger.info(f"Found {len(galmaps)} galmaps for passport {passport_label}")
    
    # Create passport directory
    passport_dir = Path("passports") / passport_label
    passport_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate galmap pages
    galmap_links = []
    for galmap in galmaps:
        galmap_dir = generate_galmap_page(galmap)
        galmap_links.append({
            "label": galmap["label"],
            "path": f"/dessins/galmaps/{galmap['label']}/index.html",
            "deg": galmap.get("deg", "N/A"),
            "g": galmap.get("g", "N/A"),
            "orbit_size": galmap.get("orbit_size", "N/A")
        })
    
    # Generate passport index page
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Passport: {passport_label}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .galmap-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }}
        .galmap-item {{ border: 1px solid #ccc; padding: 15px; text-align: center; }}
        .galmap-item a {{ text-decoration: none; color: #007bff; }}
        .galmap-item a:hover {{ text-decoration: underline; }}
        .metadata {{ background: #f5f5f5; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
        .nav {{ margin-bottom: 20px; }}
        .nav a {{ margin-right: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/dessins/index.html">← Back to Main Index</a>
        </div>
        
        <h1>Passport: {passport_label}</h1>
        
        <div class="metadata">
            <h3>Passport Metadata</h3>
            <p><strong>Degree:</strong> {passport_data.get('deg', 'N/A')}</p>
            <p><strong>Group:</strong> {passport_data.get('group', 'N/A')}</p>
            <p><strong>Genus:</strong> {passport_data.get('g', 'N/A')}</p>
            <p><strong>Geometric Type:</strong> {passport_data.get('geomtype', 'N/A')}</p>
            <p><strong>Number of Orbits:</strong> {passport_data.get('num_orbits', 'N/A')}</p>
            <p><strong>Passport Size:</strong> {passport_data.get('pass_size', 'N/A')}</p>
            <p><strong>LMFDB:</strong> <a href="https://beta.lmfdb.org/Belyi/{passport_data.get('plabel', passport_label)}" target="_blank">View on LMFDB</a></p>
        </div>
        
        <h2>Galmaps ({len(galmap_links)})</h2>
        <div class="galmap-grid">
"""
    
    for galmap in galmap_links:
        html_content += f"""
            <div class="galmap-item">
                <h3><a href="{galmap['path']}">{galmap['label']}</a></h3>
                <p><strong>Degree:</strong> {galmap['deg']}</p>
                <p><strong>Genus:</strong> {galmap['g']}</p>
                <p><strong>Orbit Size:</strong> {galmap['orbit_size']}</p>
            </div>
"""
    
    html_content += """
        </div>
    </div>
</body>
</html>"""
    
    with open(passport_dir / "index.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return passport_dir


def generate_main_index():
    """Generate the main index page"""
    # Get all passports up to degree 9 from LMFDB (no genus filter)
    passports = list(db.belyi_passports.search({"deg": {"$lte": 9}}))
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Dessins from the LMFDB</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .passport-section { margin-bottom: 30px; }
        .passport-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .passport-item { border: 1px solid #ccc; padding: 15px; text-align: center; }
        .passport-item a { text-decoration: none; color: #007bff; }
        .passport-item a:hover { text-decoration: underline; }
        .header { background: #f5f5f5; padding: 20px; margin-bottom: 20px; border-radius: 5px; }
        .filter-controls { background: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 5px; border: 1px solid #dee2e6; }
        .filter-controls label { margin-right: 20px; font-weight: bold; }
        .filter-controls input[type="checkbox"] { margin-right: 5px; }
        .passport-item.hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Dessins from the LMFDB</h1>
        </div>
        
        <div class="filter-controls">
            <span>Filter to: </span>
            <label><input type="checkbox" id="genus0-filter" onchange="applyFilters()"> Genus 0</label>
            <label><input type="checkbox" id="orbits-filter" onchange="applyFilters()"> Number of orbits > 1</label>
        </div>
        
"""
    
    # Group passports by degree
    passports_by_degree = {}
    for passport in passports:
        degree = passport.get('deg', 0)
        if degree not in passports_by_degree:
            passports_by_degree[degree] = []
        passports_by_degree[degree].append(passport)
    
    # Generate sections for each degree
    for degree in sorted(passports_by_degree.keys()):
        html_content += f"""
        <div class="passport-section">
            <h2>Degree {degree} Passports</h2>
            <div class="passport-grid">
"""
        
        for passport in passports_by_degree[degree]:
            passport_label = passport['plabel']
            genus = passport.get('g', 0)
            num_orbits = passport.get('num_orbits', 0)
            html_content += f"""
                <div class="passport-item" data-genus="{genus}" data-orbits="{num_orbits}">
                    <h3><a href="/dessins/passports/{passport_label}/index.html">{passport_label}</a></h3>
                    <p><strong>Degree:</strong> {passport.get('deg', 'N/A')}</p>
                    <p><strong>Group:</strong> {passport.get('group', 'N/A')}</p>
                    <p><strong>Genus:</strong> {genus}</p>
                    <p><strong>Orbits:</strong> {num_orbits}</p>
                </div>
"""
        
        html_content += """
            </div>
        </div>
"""
    
    html_content += """
        </div>
    </div>
    
    <script>
        function applyFilters() {
            const genus0Filter = document.getElementById('genus0-filter').checked;
            const orbitsFilter = document.getElementById('orbits-filter').checked;
            
            const passportItems = document.querySelectorAll('.passport-item');
            
            passportItems.forEach(item => {
                const genus = parseInt(item.getAttribute('data-genus'));
                const orbits = parseInt(item.getAttribute('data-orbits'));
                
                let show = true;
                
                if (genus0Filter && genus !== 0) {
                    show = false;
                }
                
                if (orbitsFilter && orbits <= 1) {
                    show = false;
                }
                
                if (show) {
                    item.classList.remove('hidden');
                } else {
                    item.classList.add('hidden');
                }
            });
        }
    </script>
</body>
</html>"""
    
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(html_content)


def main():
    parser = argparse.ArgumentParser(
        description="Generate interactive Everett diagrams from LMFDB data"
    )
    parser.add_argument(
        "--galmap",
        help="Generate diagrams for a specific galmap (e.g., '7T6-4.2.1_3.2.2_3.2.2-a')"
    )
    parser.add_argument(
        "--passport", 
        help="Generate diagrams for all galmaps in a passport (e.g., '7T6-4.2.1_3.2.2_3.2.2')"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate diagrams for all available data"
    )
    args = parser.parse_args()

    # Create directory structure
    create_directory_structure()
    
    if args.galmap:
        # Generate single galmap
        generate_galmap_page(args.galmap)
        logger.info(f"Generated diagrams for galmap {args.galmap}")
    
    elif args.passport:
        # Generate passport
        generate_passport_page(args.passport)
        logger.info(f"Generated diagrams for passport {args.passport}")
    
    elif args.all:
        # Generate all data
        # Get all passports up to degree 9 from LMFDB (no genus filter)
        passports = list(db.belyi_passports.search({"deg": {"$lte": 9}}))
        
        # Generate all passport pages
        for passport in passports:
            passport_label = passport['plabel']
            generate_passport_page(passport_label)
        
        # Get all galmaps for these passports
        for passport in passports:
            passport_label = passport['plabel']
            galmaps = get_galmaps_by_passport(passport_label)
            for galmap in galmaps:
                galmap_label = galmap['label']
                generate_galmap_page(galmap_label)
        
        generate_main_index()
        logger.info("Generated all diagrams and index pages")
    
    else:
        # Default: generate main index
        generate_main_index()
        logger.info("Generated main index page")


if __name__ == "__main__":
    main()
