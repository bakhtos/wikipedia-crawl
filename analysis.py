import networkx as nx
import numpy as np

import pickle

def prune_categories(categories):
    return categories


if __name__ == '__main__':
    # Load data from files
    with open('categories.pickle', 'rb') as file:
        categories = pickle.load(file)
    with open('links.pickle', 'rb') as file:
        links = pickle.load(file)

    # Initialize the graph
    G = nx.DiGraph(links)
    cats = prune_categories(categories)

