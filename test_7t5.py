"""
pdm run python test_7t5.py
"""


from loguru import logger
import networkx as nx

def main():
    G = nx.PlanarEmbedding()
    G.add_node('w(1,7,2,4,5,3,6)')
    G.add_node('b(1,6)')
    G.add_node('b(2,3)')
    G.add_node('b(4)')
    G.add_node('b(5)')
    G.add_node('b(7)')

    G.add_half_edge('w(1,7,2,4,5,3,6)', 'b(1,6)')
    G.add_half_edge('b(1,6)', 'w(1,7,2,4,5,3,6)')

    G.add_half_edge('w(1,7,2,4,5,3,6)', 'b(1,6)', ccw='b(1,6)')
    G.add_half_edge('b(1,6)', 'w(1,7,2,4,5,3,6)')

    G.add_half_edge('w(1,7,2,4,5,3,6)', 'b(7)', ccw='b(1,6)')
    G.add_half_edge('b(7)', 'w(1,7,2,4,5,3,6)')

    G.add_half_edge('w(1,7,2,4,5,3,6)', 'b(2,3)', ccw='b(7)')
    G.add_half_edge('b(2,3)', 'w(1,7,2,4,5,3,6)')

    G.add_half_edge('w(1,7,2,4,5,3,6)', 'b(4)', ccw='b(2,3)')
    G.add_half_edge('b(4)', 'w(1,7,2,4,5,3,6)')

    G.add_half_edge('w(1,7,2,4,5,3,6)', 'b(5)', ccw='b(4)')
    G.add_half_edge('b(5)', 'w(1,7,2,4,5,3,6)')

    G.add_half_edge('w(1,7,2,4,5,3,6)', 'b(2,3)', ccw='b(5)')
    G.add_half_edge('b(2,3)', 'w(1,7,2,4,5,3,6)')

    logger.info(G)
    logger.info(G.check_planarity())
    logger.info(G.is_planar())
    logger.info(G.check_planarity())

if __name__ == "__main__":
    main()
