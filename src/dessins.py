"""
A dessin class to construct a dessin from an lmfdb permutation triple
"""

import json

from loguru import logger
from src.galois_orbits import GaloisOrbit
import networkx as nx
import re



class Dessin:
    def __init__(self, permutation_triple: list[str], galois_orbit: GaloisOrbit):
        """
        A permutation triple is an ordered triple of permutations in cycle notation, e.g.
        ['(1,7,8,9,6)(2,3,4)', '(1,2,6)(3,4,5)(7,9,8)', '(1,2,3)(4,5)(6,7)']
        where the string '()' represents the identity permutation.
        """
        self.permutation_triple = permutation_triple
        self.galois_orbit = galois_orbit
        # if permutation_triple not in galois_orbit.get_triples_cyc():
        #     raise ValueError(f"Permutation triple {permutation_triple} not in Galois orbit {galois_orbit.get_triples_cyc()}")
    
    def __str__(self):
        return f"Dessin(permutation_triple={self.permutation_triple}, galois_orbit={self.galois_orbit})"
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        return self.permutation_triple == other.permutation_triple and self.galois_orbit == other.galois_orbit

    def get_triple(self):
        return self.permutation_triple



    def get_embedding(self):
        """
        Calculate the embedding (edge ordering around each vertex) from the permutation triple.
        The edge ordering is determined by how edges connect vertices according to the permutation triple.
        """
        def parse_cycles(perm_str, degree=None):
            if perm_str == '()':
                # Identity: return singleton cycles for each element
                if degree is None:
                    raise ValueError("Degree must be provided for identity permutation.")
                return [[i] for i in range(1, degree + 1)]
            
            # Extract all numbers mentioned in the permutation
            mentioned_numbers = set()
            cycles = re.findall(r'\(([^)]+)\)', perm_str)
            cycle_lists = []
            for cycle in cycles:
                if cycle.strip():
                    cycle_list = [int(x.strip()) for x in cycle.split(',')]
                    cycle_lists.append(cycle_list)
                    mentioned_numbers.update(cycle_list)
            
            # Find missing numbers (elements that should be in singleton cycles)
            if degree is None:
                raise ValueError("Degree must be provided to handle omitted singleton cycles.")
            
            all_numbers = set(range(1, degree + 1))
            missing_numbers = all_numbers - mentioned_numbers
            
            # Add singleton cycles for missing numbers
            for num in missing_numbers:
                cycle_lists.append([num])
            
            return cycle_lists

        def get_degree():
            # Find the largest number in any of the permutations
            max_deg = 0
            for perm in self.permutation_triple:
                numbers = re.findall(r'\d+', perm)
                if numbers:
                    max_deg = max(max_deg, max(int(n) for n in numbers))
            return max_deg

        def parse_permutation(perm_str):
            """Parse a permutation string into a dictionary mapping elements to their images."""
            if perm_str == '()':
                return {}
            
            perm_dict = {}
            cycles = re.findall(r'\(([^)]+)\)', perm_str)
            for cycle in cycles:
                if cycle.strip():
                    elements = [int(x.strip()) for x in cycle.split(',')]
                    for i in range(len(elements)):
                        perm_dict[elements[i]] = elements[(i + 1) % len(elements)]
            return perm_dict

        perm1, perm2, perm3 = self.permutation_triple
        degree = get_degree()

        # Parse the three permutations
        sigma1 = parse_permutation(perm1)  # White vertices
        sigma2 = parse_permutation(perm2)  # Black vertices
        sigma3 = parse_permutation(perm3)  # Edge connections

        # Parse cycles for vertex identification
        white_cycles = parse_cycles(perm1, degree)
        black_cycles = parse_cycles(perm2, degree)
        
        # Create embedding dictionary
        embedding = {}
        
        # Process white vertices
        for i, cycle in enumerate(white_cycles):
            vertex_id = f"white_{i+1}"
            # The edge order around a white vertex is determined by σ₃ applied to the cycle
            edge_order = []
            for element in cycle:
                # Find what σ₃ maps this element to
                if element in sigma3:
                    edge_order.append(sigma3[element])
                else:
                    edge_order.append(element)
            embedding[vertex_id] = {
                'cycle': cycle,
                'edge_order': edge_order
            }
        
        # Process black vertices
        for j, cycle in enumerate(black_cycles):
            vertex_id = f"black_{j+1}"
            # The edge order around a black vertex is determined by σ₃⁻¹ applied to the cycle
            edge_order = []
            for element in cycle:
                # Find what σ₃⁻¹ maps this element to (i.e., what maps to this element under σ₃)
                mapped_to_element = None
                for k, v in sigma3.items():
                    if v == element:
                        mapped_to_element = k
                        break
                if mapped_to_element is not None:
                    edge_order.append(mapped_to_element)
                else:
                    edge_order.append(element)
            embedding[vertex_id] = {
                'cycle': cycle,
                'edge_order': edge_order
            }
        
        return embedding

    def to_networkx_graph(self):
        """
        Converts a permutation triple to a networkx graph.
        The graph is bipartite and constructed as follows:
        - Each cycle of the first permutation is a white vertex.
        - Each cycle of the second permutation is a black vertex.
        - There is an edge between a white vertex and a black vertex if the cycle corresponding to the white vertex shares an element with the cycle corresponding to the black vertex.
        - The edge is labeled with the element that is shared between the two cycles.

        For the permutation triple
        ['(1,7,8,9,6)(2,3,4)', '(1,2,6)(3,4,5)(7,9,8)', '(1,2,3)(4,5)(6,7)']
        we describe an example edge:
        - (1,7,8,9,6) corresponds to a white vertex
        - (1,2,6) corresponds to a black vertex
        - There is an edge between the white vertex and the black vertex labeled with the element 1.
        - There is also an edge between the white vertex and the black vertex labeled with the element 6.

        Note that the string '()' corresponds to the identity permutation which is equivalent to '(1)(2)(3)(4)(5)(6)(7)(8)(9)' in the degree 9 case.
        Note that all permutations should have the same degree.
        If all permutations are the identity, the graph has a single edge connecting a white vertex to a black vertex.
        """
        def parse_cycles(perm_str, degree=None):
            if perm_str == '()':
                # Identity: return singleton cycles for each element
                if degree is None:
                    raise ValueError("Degree must be provided for identity permutation.")
                return [[i] for i in range(1, degree + 1)]
            
            # Extract all numbers mentioned in the permutation
            mentioned_numbers = set()
            cycles = re.findall(r'\(([^)]+)\)', perm_str)
            cycle_lists = []
            for cycle in cycles:
                if cycle.strip():
                    cycle_list = [int(x.strip()) for x in cycle.split(',')]
                    cycle_lists.append(cycle_list)
                    mentioned_numbers.update(cycle_list)
            
            # Find missing numbers (elements that should be in singleton cycles)
            if degree is None:
                raise ValueError("Degree must be provided to handle omitted singleton cycles.")
            
            all_numbers = set(range(1, degree + 1))
            missing_numbers = all_numbers - mentioned_numbers
            
            # Add singleton cycles for missing numbers
            for num in missing_numbers:
                cycle_lists.append([num])
            
            return cycle_lists

        def get_degree():
            # Find the largest number in any of the permutations
            max_deg = 0
            for perm in self.permutation_triple:
                numbers = re.findall(r'\d+', perm)
                if numbers:
                    max_deg = max(max_deg, max(int(n) for n in numbers))
            return max_deg

        perm1, perm2 = self.permutation_triple[0], self.permutation_triple[1]
        degree = get_degree()

        # Handle all identity case
        if perm1 == '()' and perm2 == '()':
            G = nx.MultiGraph()
            G.add_node("white_1", bipartite=0)
            G.add_node("black_1", bipartite=1)
            G.add_edge("white_1", "black_1", label=1)
            return G

        # Parse cycles
        white_cycles = parse_cycles(perm1, degree)
        black_cycles = parse_cycles(perm2, degree)

        G = nx.MultiGraph()
        # Add white vertices
        for i, cycle in enumerate(white_cycles):
            G.add_node(f"white_{i+1}", bipartite=0, cycle=cycle)
        # Add black vertices
        for j, cycle in enumerate(black_cycles):
            G.add_node(f"black_{j+1}", bipartite=1, cycle=cycle)
        # Add edges (one for each shared element)
        for i, wcycle in enumerate(white_cycles):
            for j, bcycle in enumerate(black_cycles):
                shared = set(wcycle) & set(bcycle)
                for element in shared:
                    G.add_edge(f"white_{i+1}", f"black_{j+1}", label=element)
        return G

    def adjacency_matrix(self):
        G = self.to_networkx_graph()
        return nx.adjacency_matrix(G)

    def is_planar(self):
        """
        Checks if the dessin is planar.
        """
        G = self.to_networkx_graph()
        b, embedding = nx.check_planarity(G)
        if b:
            return embedding
        else:
            return None

    def to_json(self, index: int):
        G = self.to_networkx_graph()
        embedding = self.get_embedding()
        logger.info(f"G: {G}")
        
        # Include node attributes
        nodes = []
        for n in G.nodes():
            node_data = {"id": str(n)}
            if 'bipartite' in G.nodes[n]:
                node_data["bipartite"] = G.nodes[n]['bipartite']
            if 'cycle' in G.nodes[n]:
                node_data["cycle"] = list(G.nodes[n]['cycle'])
            if n in embedding:
                node_data["embedding"] = embedding[n]
            nodes.append({"data": node_data})
        
        # Include edge attributes
        edges = []
        for u, v, data in G.edges(data=True):
            edge_data = {"source": str(u), "target": str(v)}
            if 'label' in data:
                edge_data["label"] = data['label']
            edges.append({"data": edge_data})
        
        # Get the combinatorial map layout
        layout = self.get_combinatorial_map_layout()
        
        data = {
            "nodes": nodes,
            "edges": edges,
            "permutation_triple": self.permutation_triple,
            "layout": layout
        }
        with open(f"docs/{self.galois_orbit.get_label()}_{index}.json", "w") as f:  # put in /docs so GitHub Pages can find it
            json.dump(data, f)

    def get_dessin_layout(self):
        """
        Generate a layout for the dessin that respects the edge ordering constraints.
        This is a more sophisticated approach than force-directed layout.
        """
        import math
        
        # Get the embedding information
        embedding = self.get_embedding()
        
        # Find the vertex with the most edges (usually the white vertex)
        max_edges = 0
        central_vertex = None
        for vertex_id, data in embedding.items():
            if len(data['edge_order']) > max_edges:
                max_edges = len(data['edge_order'])
                central_vertex = vertex_id
        
        if not central_vertex:
            return {}
        
        # Start with the central vertex at the origin
        layout = {central_vertex: {'x': 0, 'y': 0}}
        
        # Get the edge ordering for the central vertex
        central_cycle = embedding[central_vertex]['edge_order']
        
        # Get the graph to find edges
        G = self.to_networkx_graph()
        
        # Place connected vertices in a circle around the central vertex
        # The angle between vertices should respect the edge ordering
        connected_vertices = set()
        for u, v, data in G.edges(data=True):
            if u == central_vertex:
                connected_vertices.add(v)
            elif v == central_vertex:
                connected_vertices.add(u)
        
        # Calculate positions for connected vertices
        radius = 200  # Distance from central vertex
        angle_step = 2 * math.pi / len(central_cycle)
        
        # Map edge labels to their positions in the cycle
        edge_positions = {label: i for i, label in enumerate(central_cycle)}
        
        # Place vertices based on their edge connections
        for vertex_id in connected_vertices:
            # Find the edge labels that connect this vertex to the central vertex
            connecting_labels = []
            for u, v, data in G.edges(data=True):
                if ((u == central_vertex and v == vertex_id) or
                    (u == vertex_id and v == central_vertex)):
                    connecting_labels.append(data['label'])
            
            # Use the first connecting label to determine position
            if connecting_labels:
                first_label = connecting_labels[0]
                if first_label in edge_positions:
                    angle = edge_positions[first_label] * angle_step
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)
                    layout[vertex_id] = {'x': x, 'y': y}
        
        # For vertices not directly connected to central vertex, place them further out
        outer_radius = 400
        remaining_vertices = set(embedding.keys()) - {central_vertex} - connected_vertices
        
        for i, vertex_id in enumerate(remaining_vertices):
            angle = (i * 2 * math.pi) / len(remaining_vertices)
            x = outer_radius * math.cos(angle)
            y = outer_radius * math.sin(angle)
            layout[vertex_id] = {'x': x, 'y': y}
        
        return layout

    def get_combinatorial_map_layout(self):
        """
        Generate a layout using combinatorial map theory.
        This properly respects the rotation system determined by the permutation cycles.
        """
        import math
        
        # Get the embedding information
        embedding = self.get_embedding()
        G = self.to_networkx_graph()
        
        # Build the rotation system from the embedding
        rotation_system = {}
        for vertex_id, data in embedding.items():
            rotation_system[vertex_id] = data['edge_order']
        
        # Find the vertex with the most edges (usually the white vertex)
        max_edges = 0
        central_vertex = None
        for vertex_id, edge_order in rotation_system.items():
            if len(edge_order) > max_edges:
                max_edges = len(edge_order)
                central_vertex = vertex_id
        
        if not central_vertex:
            return {}
        
        # Start with the central vertex at the origin
        layout = {central_vertex: {'x': 0, 'y': 0}}
        
        # Get the rotation system for the central vertex
        central_rotation = rotation_system[central_vertex]
        
        # Create a mapping from edge labels to their positions in the rotation
        edge_positions = {label: i for i, label in enumerate(central_rotation)}
        
        # Find all vertices connected to the central vertex
        connected_vertices = set()
        edge_connections = {}  # Maps edge label to connected vertex
        
        for u, v, data in G.edges(data=True):
            if u == central_vertex:
                connected_vertices.add(v)
                edge_connections[data['label']] = v
            elif v == central_vertex:
                connected_vertices.add(u)
                edge_connections[data['label']] = u
        
        # Position connected vertices according to the rotation system
        radius = 200
        angle_step = 2 * math.pi / len(central_rotation)
        
        for label, position in edge_positions.items():
            if label in edge_connections:
                vertex_id = edge_connections[label]
                angle = position * angle_step
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                layout[vertex_id] = {'x': x, 'y': y}
        
        # For vertices not directly connected to central vertex, place them further out
        outer_radius = 400
        remaining_vertices = set(embedding.keys()) - {central_vertex} - connected_vertices
        
        for i, vertex_id in enumerate(remaining_vertices):
            angle = (i * 2 * math.pi) / len(remaining_vertices)
            x = outer_radius * math.cos(angle)
            y = outer_radius * math.sin(angle)
            layout[vertex_id] = {'x': x, 'y': y}
        
        return layout

    def get_planar_embedding_layout(self):
        """
        Generate a planar embedding layout that respects the rotation system.
        This approach tries to create a more natural planar embedding rather than
        forcing a star-like layout.
        """
        import math
        
        # Get the embedding information
        embedding = self.get_embedding()
        G = self.to_networkx_graph()
        
        # Build the rotation system from the embedding
        rotation_system = {}
        for vertex_id, data in embedding.items():
            rotation_system[vertex_id] = data['edge_order']
        
        # Find the vertex with the most edges (usually the white vertex)
        max_edges = 0
        central_vertex = None
        for vertex_id, edge_order in rotation_system.items():
            if len(edge_order) > max_edges:
                max_edges = len(edge_order)
                central_vertex = vertex_id
        
        if not central_vertex:
            return {}
        
        # Start with the central vertex at the origin
        layout = {central_vertex: {'x': 0, 'y': 0}}
        
        # Get the rotation system for the central vertex
        central_rotation = rotation_system[central_vertex]
        
        # Create a mapping from edge labels to their positions in the rotation
        edge_positions = {label: i for i, label in enumerate(central_rotation)}
        
        # Find all vertices connected to the central vertex
        connected_vertices = set()
        edge_connections = {}  # Maps edge label to connected vertex
        
        for u, v, data in G.edges(data=True):
            if u == central_vertex:
                connected_vertices.add(v)
                edge_connections[data['label']] = v
            elif v == central_vertex:
                connected_vertices.add(u)
                edge_connections[data['label']] = u
        
        # For a more natural planar embedding, let's try a different approach
        # Instead of placing vertices in a circle, let's try to create a more
        # balanced layout that respects the edge ordering
        
        # Calculate positions based on the rotation system
        radius = 150
        angle_step = 2 * math.pi / len(central_rotation)
        
        # Position vertices according to their edge labels in the rotation
        for label, position in edge_positions.items():
            if label in edge_connections:
                vertex_id = edge_connections[label]
                angle = position * angle_step
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                layout[vertex_id] = {'x': x, 'y': y}
        
        # For vertices not directly connected to central vertex, place them strategically
        outer_radius = 300
        remaining_vertices = set(embedding.keys()) - {central_vertex} - connected_vertices
        
        for i, vertex_id in enumerate(remaining_vertices):
            angle = (i * 2 * math.pi) / len(remaining_vertices)
            x = outer_radius * math.cos(angle)
            y = outer_radius * math.sin(angle)
            layout[vertex_id] = {'x': x, 'y': y}
        
        return layout