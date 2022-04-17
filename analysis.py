import networkx as nx
import community
import demon
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import pickle
import random
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

    ## K-clique
    print("Starting K-clique...")
    comm_kclique = nx.algorithms.community.k_clique_communities(G, k=15)
    comm_kclique = list(comm_kclique)
    print("K-cliques found.")
    dist_kclique = Counter()
    nums_kclique = Counter()
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
        for node in G.nodes():
            if node in comm: nums_kclique[node] += 1

    print("K-clique results calculated")
    results["k-clique"] = dict(size_distribution=dist_kclique, communities=comm_kclique,
                               node_participation=nums_kclique,
                               maximal_community=max_kclique)
    ## Louvain
    print("Starting Louvain...")
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

    ## Demon

    print("Starting Demon...")
    dm = demon.Demon(graph=G, epsilon=0.25, min_community_size=4)
    comm_demon = dm.execute()
    print("Demon communities found.")
    dist_demon = Counter()
    nums_demon = Counter()
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
        for node in G.nodes():
            if node in comm: nums_demon[node] += 1
    print("Demon results calculated.")

    results["demon"] = dict(distribution=dist_demon, communities=comm_demon,
                            node_participation=nums_demon,
                              maximal_community=max_demon)

    return results


def spreading(G, beta=0.05, gamma = 0.1, SIR=False, t_max=1000, patient_zero='Mathematics'):

    infection_started = False
    for node in G.nodes:
        if node == patient_zero:
            G.nodes[node]['Infected'] = 'I'
            G.nodes[node]['Infection_time'] = 0
            infection_started = True
        else:
            G.nodes[node]['Infected'] = 'S'
            G.nodes[node]['Infection_time'] = None

    if not infection_started:
        raise ValueError("Patient zero node was not found")

    infection_progress_i = Counter()
    infection_progress_s = Counter()
    infection_progress_r = Counter()
    infection_progress_r[0] = 0
    infection_progress_i[0] = 0
    infection_progress_s[0] = len(G.nodes)
    t = 1

    while t<t_max:
        to_infect = set()
        for node, adj in G.adjacency():
            if G.nodes[node]['Infected'] == 'I':
                infects = {n for n in adj if G.nodes[n]['Infected'] == 'S'
                           and random.random()<beta}
                to_infect.update(infects)

        infection_progress_i[t] = len(to_infect)
        for node in G.nodes():
            if node in to_infect:
                G.nodes[node]['Infected'] = 'I'
                G.nodes[node]['Infection_time'] = t
                infection_progress_s[t] -= 1
            elif G.nodes[node]['Infected'] == 'I' and random.random() < gamma:
                if SIR:
                    G.nodes[node]['Infected'] = 'R'
                    infection_progress_r[t] += 1
                    infection_progress_s[t] += 0
                else:
                    G.nodes[node]['Infected'] = 'S'
                    infection_progress_s[t] += 1
                G.nodes[node]['Infection_time'] = None
                infection_progress_i[t] -= 1


        infection_progress_s[t] += 0
        infection_progress_i[t] += 0
        infection_progress_r[t] += 0
                
        t += 1
        
    return infection_progress_s,infection_progress_i,infection_progress_r
                    

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

    '''
    comms = community_discovery(G)
    with open('community.pickle', 'wb') as file:
        pickle.dump(comms, file)
    '''
    experiments = [
        (0.01, 0.1, False, 100),
        (0.1, 0.01, False, 100),
        (0.01, 0.1, True, 100),
        (0.1, 0.01, True, 100)
    ]
    for beta, gamma, SIR, t_max in experiments:
        s,i,r = spreading(G, beta=beta, gamma=gamma, SIR=SIR, t_max=t_max)
        s = pd.Series(s).sort_index()
        s.cumsum().plot(logy=False, marker='.')
        i = pd.Series(i).sort_index()
        i.cumsum().plot(logy=False, marker='.')
        if SIR:
            r = pd.Series(r).sort_index()
            r.cumsum().plot(logy=False, marker='.')
            plt.legend(['S', 'I', 'R'])
            plt.title(f"SIR process with inf. rate = {beta}, rec. rate = {gamma}")
        else:
            plt.legend(['S', 'I'])
            plt.title(f"SIS process with inf. rate = {beta}, rec. rate = {gamma}")
        plt.show()
