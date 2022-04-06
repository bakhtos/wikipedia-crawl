import networkx as nx
import numpy as np

import pickle
import re

def prune_pages(links, categories):
    '''Remove pages dedicated to numbers and identifiers.
    Parameters:
    dict links: dictionary of the form str -> set(str), containing links
        of Wikipedia pages from key to pages in the set.
    dict categories: dictionary of the form str -> set(str), containing
        Wikipedia categories for pages.
    Return:
    dict new_links: same as links, but all pages with "(number)" and "(identifier)"
        in the title have been removed both as a key and inside any set.
    dict categories: same as input categories, but with "(number)" and "(identifier)"
        pages removed. NOTE: not the copy of input but the same thing, ie
        original 'categories' gets modified.
    '''
    # New links to return
    new_links = dict()
    # Loop over links
    for key in links:
        if "(identifier)" in key or "(number)" in key:
            # Remove page from categories also
            del categories[key]
        else:
            new_set = set()
            for link in links[key]:
                # Skip unnecessary pages
                if "(identifier)" in link or "(number)" in link: continue
                else: new_set.add(link)
            new_links[key] = new_set
    return new_links, categories

def prune_categories(categories, prune_dates=False):
    ''' Remove wikipedia meta-categories from pages' categories.
    Parameters:
    dict categories: dictionary of the form str -> set(str) containing
        wikipedia categories for each pages (pages are keys)
    bool prune_dates: if True, prune also categories related to dates.
        (default False)
    Return:
    dict of the form str -> set(str), similar to input but with categories pruned
    '''

    to_return = dict() # New dict for pruned categories

    # Regexes needed to prune
    prune = re.compile(r"[Aa]rticle|[Pp]ages|Wiki|Use \w* dates|Use .*English|[Tt]emplate")
    dates = re.compile(r"\d\d\d\d|century")
    
    # Iterate over data
    for page, cats in categories.items():
        new_cats = set()
        for cat in cats:
            # Skip category if macted by pruning regexes
            if prune.search(cat): continue
            if prune_dates and dates.search(cat): continue
            else: new_cats.add(cat) 
        # Save pruned categories
        to_return[page] = new_cats

    return to_return

def WS_model(N, k, p):
    G = nx.Graph()
    # Add N nodes from 0 to N-1
    G.add_nodes_from(range(N))
    # for each node
    for i in range(N):
        # for each distance from node (1 to k/2)
        for j in range(1,k//2+1):
            # node 'to the left of i', accounting for cycling below 0
            v1 = i-j if i-j>=0 else N+i-j
            # node 'to the right of i', accouting for cycling above N
            v2 = i+j if i+j<N else i+j-N
            # Add the two edges
            G.add_edge(i, v1)
            G.add_edge(i, v2)
    # New graph for storing rewired edges
    G2 = nx.Graph()
    # Iterate over edges
    for edge in G.edges:
        # with probability p...
        if random.random()<p:
            # choose a random end of the edge
            node = random.choice(edge)
            # make a list of all nodes and remove the chosen node
            nodes = list(range(N))
            nodes.remove(node)
            # randomly choose another node from available ones
            node2 = random.choice(nodes)
            # this is the new edge
            edge = (node, node2)
        # Add an edge (either the same or rewired one) to graph
        G2.add_edge(*edge)
    return G2

def BA_model(N, m):
    # Make a complete graph
    G = nx.complete_graph(m)
    # Add remaining nodes
    for i in range(m,N):
        # Create a sorted list of nodes
        nodes = sorted(G.nodes)
        # Create a sorted (by node) list of degrees
        degrees = [val for key,val in sorted(G.degree)]
        # if we started we one node (m=1), its degree is 0,
        # but the probability to connect should be 1
        if degrees == [0]: degrees=[1]
        js = random.choices(nodes, degrees, k=m)
        for j in js: G.add_edge(i,j)
    return G

if __name__ == '__main__':
    # Load data from files
    with open('categories.pickle', 'rb') as file:
        categories = pickle.load(file)
    with open('links.pickle', 'rb') as file:
        links = pickle.load(file)

    # Initialize the graph
    G = nx.DiGraph(links)
    # Prune categories
    categories = prune_categories(categories, True)
