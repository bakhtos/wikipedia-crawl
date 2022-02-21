import networkx as nx
import numpy as np

import pickle
import re

def prune_categories(categories, prune_dates=False):
    to_return = dict()
    prune = re.compile(r"[Aa]rticle|[Pp]ages|Wiki|Use \w* dates|Use .*English|[Tt]emplate")
    dates = re.compile(r"\d\d\d\d|century")
    for page, cats in categories.items():
        new_cats = set()
        for cat in cats:
            if prune.search(cat): continue
            if prune_dates and dates.search(cat): continue
            else: new_cats.add(cat) 
        to_return[page] = new_cats
    return to_return


if __name__ == '__main__':
    # Load data from files
    with open('categories.pickle', 'rb') as file:
        categories = pickle.load(file)
    with open('links.pickle', 'rb') as file:
        links = pickle.load(file)

    # Initialize the graph
    G = nx.DiGraph(links)
    cats = prune_categories(categories, True)
