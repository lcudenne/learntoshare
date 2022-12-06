import networkx as nx
import matplotlib.pyplot as plt
import argparse



# ------------------------------------------------------------------------------

def draw_overlay(filenames):

    G = nx.DiGraph()

    for filename in filenames:
        with open(filename) as logfile:
            for line in logfile:
                if "DHT ADD" in line:
                    linesplit = line.rstrip().split(' ')
                    node_from = linesplit[9]
                    node_to = linesplit[12]
                    G.add_edge(node_from, node_to)
                    print(node_from, "to", node_to)

    nx.draw(G)
    plt.show()
    return None






# ------------------------------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog = 'draw_overlay.py',
        description = 'Overlay graph building',
        epilog = 'https://github.com/lcudenne/learntoshare')

    parser.add_argument("-f", "--logfiles", nargs="+", type=str, default="log", required=False,
                        help="log file parsed to build the overlay graph (default is ./log)")
    args = parser.parse_args()

    draw_overlay(args.logfiles)
    
    exit(0)
