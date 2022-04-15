import networkx as nx
import community
import demon
import numpy as np

import pickle
import re
from collections import Counter

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

def make_random_as(G):
    ''' Create Erdos-Renyi and Barabasi-Albert random graph using given graph G.
    Parameters:
    nx.Graph G: Graph whose number of edges and nodes will be used for generation.
    Return:
    nx.Graph ER_graph, BA_graph: generated graphs.
    '''
    n = len(G.nodes) # number of nodes
    l = len(G.edges) # number of edges
    m = int(l/n) # number of edges to add in preferential attachement
    p = l/(n*(n-1)) # probaility for edge to exist
    ER_graph = nx.erdos_renyi_graph(n, p, seed=42, directed=True)
    BA_graph = nx.barabasi_albert_graph(n, m, seed=42)
    return ER_graph, BA_graph

def community_discovery(D):
    ''' Run several community discovery methods.
    Parameters:
    nx.DiGraph D: Graph to be studied.'''

    G = D.to_undirected(as_view=True)
    results = dict()
    '''
    ## K-clique
    comm_kclique = nx.algorithms.community.k_clique_communities(G, k=4)
    comm_kclique = list(comm_kclique)
    dist_kclique = Counter()
    max_size = 0
    max_kclique = []
    for comm in comm_kclique:
        size = len(comm)
        dist_kclique[size] += 1
        if size > max_size:
            max_size = size
            max_kclique = [comm]
        elif size == max_size:
            max_kclique.append(comm)

    results["k-clique"] = dict(distribution=dist_clique, communities=comm_clique,
                               maximal_community=max_kclique)
    '''
    ## Louvain
    print("Staring Louvain...")
    partition = community.best_partition(G)
    print("Louvain partition found.")
    modularity_louvain = community.modularity(partition, G)
    print("Louvain modularity calculated")
    comm_louvain = dict()
    for node, comm_id in partition.items():
        if comm_id not in comm_louvain:
            comm_louvain[comm_id] = set(node)
        else:
            comm_louvain[comm_id].add(node)

    comm_louvain = list(comm_louvain.values())
    dist_louvain = Counter()
    max_size = 0
    max_louvain = []
    for comm in comm_louvain:
        size = len(comm)
        dist_louvain[size] += 1
        if size > max_size:
            max_size = size
            max_louvain = [comm]
        elif size == max_size:
            max_louvain.append(comm)

    print("Louvain results calculated.")
    results["louvain"] = dict(distribution=dist_louvain, communities=comm_louvain,
                              maximal_community=max_louvain)

    '''
    ## Demon

    dm = demon.Demon(graph=G, epsilon=0.25, min_community_size=4)
    comm_demon = dm.execute()
    dist_demon = Counter()
    max_size = 0
    max_demon = []
    for comm in comm_demon:
        size = len(comm)
        dist_demon[size] += 1
        if size > max_size:
            max_size = size
            max_demon = [comm]
        elif size == max_size:
            max_demon.append(comm)
    results["demon"] = dict(distribution=dist_demon, communities=comm_demon,
                              maximal_community=max_demon)

    '''

    return results

if __name__ == '__main__':
    # Load data from files
    with open('categories_clean.pickle', 'rb') as file:
        categories = pickle.load(file)
    with open('links_clean.pickle', 'rb') as file:
        links = pickle.load(file)

    # Initialize the graph
    G = nx.DiGraph(links)
    
    # Load random graphs
    BA_graph = nx.read_gpickle("random_BA.pickle")
    ER_graph = nx.read_gpickle("random_ER.pickle")

    comms = community_discovery(G)
    print(comms)
