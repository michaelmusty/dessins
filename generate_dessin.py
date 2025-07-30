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

# Mock LMFDB data - replace with actual lmfdb_lite interface
# This is a placeholder structure based on the schema you provided
LMFDB_DATA = {
    "galmaps": {
        "7T6-4.2.1_3.2.2_3.2.2-a": {
            "label": "7T6-4.2.1_3.2.2_3.2.2-a",
            "plabel": "7T6-4.2.1_3.2.2_3.2.2",
            "deg": 7,
            "triples_cyc": [["(1,6,5,3)", "(4,7)", "(1,2,3)", "(4,5)", "(6,7)"]],
            "group": "7T6",
            "g": 0,
            "geomtype": "S"
        },
        "7T6-4.2.1_3.2.2_3.2.2-b": {
            "label": "7T6-4.2.1_3.2.2_3.2.2-b", 
            "plabel": "7T6-4.2.1_3.2.2_3.2.2",
            "deg": 7,
            "triples_cyc": [["(1,2,3,4)", "(5,6,7)", "(1,5)", "(2,6)", "(3,7)", "(4)"]],
            "group": "7T6",
            "g": 0,
            "geomtype": "S"
        }
    },
    "passports": {
        "7T6-4.2.1_3.2.2_3.2.2": {
            "plabel": "7T6-4.2.1_3.2.2_3.2.2",
            "deg": 7,
            "num_orbits": 2,
            "pass_size": 2,
            "group": "7T6",
            "g": 0,
            "geomtype": "S"
        }
    }
}

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
    """Get galmap data from LMFDB (replace with actual lmfdb_lite call)"""
    return LMFDB_DATA["galmaps"].get(galmap_label)


def get_lmfdb_passport(passport_label):
    """Get passport data from LMFDB (replace with actual lmfdb_lite call)"""
    return LMFDB_DATA["passports"].get(passport_label)


def get_galmaps_by_passport(passport_label):
    """Get all galmaps for a given passport (replace with actual lmfdb_lite call)"""
    galmaps = []
    for label, galmap in LMFDB_DATA["galmaps"].items():
        if galmap["plabel"] == passport_label:
            galmaps.append(galmap)
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


def generate_galmap_page(galmap_data):
    """Generate an HTML page for a single galmap showing all its diagrams"""
    galmap_label = galmap_data["label"]
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
        if len(triple) >= 2:  # Need at least white and black permutations
            white_perm = triple[0]
            black_perm = triple[1]
            
            # Generate the diagram
            diagram_filename = f"diagram_{i+1}.html"
            diagram_path = galmap_dir / diagram_filename
            
            try:
                generate_single_diagram(white_perm, black_perm, diagram_path)
                diagram_files.append({
                    "filename": diagram_filename,
                    "white": white_perm,
                    "black": black_perm,
                    "index": i+1
                })
                logger.info(f"Generated diagram {i+1}: {white_perm} vs {black_perm}")
            except Exception as e:
                logger.error(f"Failed to generate diagram {i+1}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Generate the galmap index page
    generate_galmap_index(galmap_data, diagram_files, galmap_dir)
    
    return galmap_dir


def generate_single_diagram(white_perm, black_perm, output_path):
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

    # Ensure all vertices are placed before drawing edges
    for v in vertices.keys():
        if v not in pos:
            # Place unplaced vertices at default positions
            if v.startswith("w"):
                pos[v] = (0, 0)
                orient[v] = 0.0
            else:
                pos[v] = (1.4, 0)
                orient[v] = 0.0
    
    # Draw all edges (simplified traversal)
    for v in list(vertices.keys()):
        for idx, lab in enumerate(vertices[v]["cycle"]):
            if lab not in visited:
                draw_edge(v, idx)

    # Generate HTML
    html_content = generate_interactive_html(pos, straight, curves, stubs, white_perm, black_perm)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def generate_interactive_html(pos, straight, curves, stubs, white_perm, black_perm):
    """Generate the interactive HTML content (simplified version)"""
    # Build vertices data
    vertices_data = []
    for v, (x, y) in pos.items():
        face = "white" if v.startswith("w") else "black"
        col = "black" if face == "white" else "white"
        vertices_data.append(f'                {{ id: "{v}", x: {x}, y: {y}, color: "{face}", textColor: "{col}" }}')
    
    # Build edges data (simplified)
    straight_edges_data = []
    for p1, p2, lab in straight:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        straight_edges_data.append(f'                {{ start: [{p1[0]}, {p1[1]}], end: [{p2[0]}, {p2[1]}], label: "{lab}", labelX: {mx}, labelY: {my} }}')
    
    curved_edges_data = []
    for i, (P0s, P1, P2, P3s, lab) in enumerate(curves):
        mx, my = (P0s[0] + P3s[0]) / 2, (P0s[1] + P3s[1]) / 2
        curved_edges_data.append(f'                {{ id: {i}, start: [{P0s[0]}, {P0s[1]}], end: [{P3s[0]}, {P3s[1]}], control1: [{P1[0]}, {P1[1]}], control2: [{P2[0]}, {P2[1]}], label: "{lab}", labelX: {mx}, labelY: {my} }}')
    
    # Basic HTML template
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Everett Diagram: {white_perm} vs {black_perm}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Everett Diagram</h1>
        <p><strong>White permutation:</strong> {white_perm}</p>
        <p><strong>Black permutation:</strong> {black_perm}</p>
        <div id="graph"></div>
    </div>

    <script>
        const width = 800;
        const height = 600;
        const margin = 50;

        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("border", "1px solid #ccc");

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

        // Calculate bounds and scales
        const allX = [...graphData.vertices.map(v => v.x), ...graphData.straightEdges.flatMap(e => [e.start[0], e.end[0]]), ...graphData.curvedEdges.flatMap(e => [e.start[0], e.end[0], e.control1[0], e.control2[0]])];
        const allY = [...graphData.vertices.map(v => v.y), ...graphData.straightEdges.flatMap(e => [e.start[1], e.end[1]]), ...graphData.curvedEdges.flatMap(e => [e.start[1], e.end[1], e.control1[1], e.control2[1]])];
        
        const minX = Math.min(...allX);
        const maxX = Math.max(...allX);
        const minY = Math.min(...allY);
        const maxY = Math.max(...allY);
        
        const padding = Math.max(maxX - minX, maxY - minY) * 0.1;
        const xScale = d3.scaleLinear()
            .domain([minX - padding, maxX + padding])
            .range([margin, width - margin]);

        const yScale = d3.scaleLinear()
            .domain([minY - padding, maxY + padding])
            .range([height - margin, margin]);

        // Draw edges
        svg.selectAll(".straight-edge")
            .data(graphData.straightEdges)
            .enter()
            .append("line")
            .attr("class", "edge")
            .attr("x1", d => xScale(d.start[0]))
            .attr("y1", d => yScale(d.start[1]))
            .attr("x2", d => xScale(d.end[0]))
            .attr("y2", d => yScale(d.end[1]));

        svg.selectAll(".curved-edge")
            .data(graphData.curvedEdges)
            .enter()
            .append("path")
            .attr("class", "curved-edge edge")
            .attr("d", d => `M ${{xScale(d.start[0])}} ${{yScale(d.start[1])}} C ${{xScale(d.control1[0])}} ${{yScale(d.control1[1])}} ${{xScale(d.control2[0])}} ${{yScale(d.control2[1])}} ${{xScale(d.end[0])}} ${{yScale(d.end[1])}}`);

        // Draw vertices
        svg.selectAll(".vertex")
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

        // Add labels
        svg.selectAll(".vertex-text")
            .data(graphData.vertices)
            .enter()
            .append("text")
            .attr("class", "vertex-text")
            .attr("x", d => xScale(d.x))
            .attr("y", d => yScale(d.y))
            .attr("fill", d => d.textColor)
            .text(d => d.id);

        // Add edge labels
        const edgeLabels = svg.selectAll(".edge-label")
            .data([...graphData.straightEdges, ...graphData.curvedEdges])
            .enter()
            .append("g")
            .attr("class", "edge-label-group");

        edgeLabels.append("rect")
            .attr("class", "edge-label-bg")
            .attr("x", d => xScale(d.labelX) - 8)
            .attr("y", d => yScale(d.labelY) - 8)
            .attr("width", 16)
            .attr("height", 16);

        edgeLabels.append("text")
            .attr("class", "edge-label")
            .attr("x", d => xScale(d.labelX))
            .attr("y", d => yScale(d.labelY))
            .text(d => d.label);
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
            <a href="../index.html">← Back to Passport Index</a>
            <a href="../../index.html">← Back to Main Index</a>
        </div>
        
        <h1>Galmap: {galmap_label}</h1>
        
        <div class="metadata">
            <h3>Metadata</h3>
            <p><strong>Passport:</strong> {passport_label}</p>
            <p><strong>Degree:</strong> {galmap_data.get('deg', 'N/A')}</p>
            <p><strong>Group:</strong> {galmap_data.get('group', 'N/A')}</p>
            <p><strong>Genus:</strong> {galmap_data.get('g', 'N/A')}</p>
            <p><strong>Geometric Type:</strong> {galmap_data.get('geomtype', 'N/A')}</p>
        </div>
        
        <h2>Diagrams ({len(diagram_files)})</h2>
        <div class="diagram-grid">
"""
    
    for diagram in diagram_files:
        html_content += f"""
            <div class="diagram-item">
                <h3>Diagram {diagram['index']}</h3>
                <p><strong>White:</strong> {diagram['white']}</p>
                <p><strong>Black:</strong> {diagram['black']}</p>
                <iframe src="{diagram['filename']}"></iframe>
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
            "path": f"../galmaps/{galmap['label']}/index.html",
            "deg": galmap.get("deg", "N/A"),
            "g": galmap.get("g", "N/A")
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
            <a href="../index.html">← Back to Main Index</a>
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
    # Get all passports (replace with actual LMFDB query)
    passports = list(LMFDB_DATA["passports"].keys())
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>LMFDB Everett Diagrams</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .passport-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .passport-item { border: 1px solid #ccc; padding: 15px; text-align: center; }
        .passport-item a { text-decoration: none; color: #007bff; }
        .passport-item a:hover { text-decoration: underline; }
        .header { background: #f5f5f5; padding: 20px; margin-bottom: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LMFDB Everett Diagrams</h1>
            <p>Interactive visualizations of Belyi maps from the L-functions and Modular Forms Database</p>
        </div>
        
        <h2>Passports</h2>
        <div class="passport-grid">
"""
    
    for passport_label in passports:
        passport_data = LMFDB_DATA["passports"][passport_label]
        html_content += f"""
            <div class="passport-item">
                <h3><a href="passports/{passport_label}/index.html">{passport_label}</a></h3>
                <p><strong>Degree:</strong> {passport_data.get('deg', 'N/A')}</p>
                <p><strong>Group:</strong> {passport_data.get('group', 'N/A')}</p>
                <p><strong>Genus:</strong> {passport_data.get('g', 'N/A')}</p>
                <p><strong>Orbits:</strong> {passport_data.get('num_orbits', 'N/A')}</p>
            </div>
"""
    
    html_content += """
        </div>
    </div>
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
        galmap_data = get_lmfdb_galmap(args.galmap)
        if galmap_data:
            generate_galmap_page(galmap_data)
            logger.info(f"Generated diagrams for galmap {args.galmap}")
        else:
            logger.error(f"Galmap {args.galmap} not found")
    
    elif args.passport:
        # Generate passport
        generate_passport_page(args.passport)
        logger.info(f"Generated diagrams for passport {args.passport}")
    
    elif args.all:
        # Generate all data
        for passport_label in LMFDB_DATA["passports"].keys():
            generate_passport_page(passport_label)
        generate_main_index()
        logger.info("Generated all diagrams and index pages")
    
    else:
        # Default: generate main index
        generate_main_index()
        logger.info("Generated main index page")


if __name__ == "__main__":
    main()
