import pickle
import argparse
from nltk.corpus import wordnet as wn

#create dictionary of "similar" words from top 30K word list, where "similar" means that words are within mindist nodes of each other in wordnet
def wordnet_simdict(word_list_file, mindist, simdict_file):
    words = []
    with open(word_list_file, "r") as rf:
        for line in rf:
            w = line.strip()
            words.append(w)
    sim_dict = dict()
    i=0
#compute pairwise wordnet distance for entire word list, only add to dictionary if within mindist nodes
    for w1 in words:
        if i % 100 == 0:
            print("building word similarity: ",w1," - ", i)
        if w1 not in sim_dict:
            sim_dict[w1]=[]
        for w2 in words[i+1:]:
            if w2 not in sim_dict:
                sim_dict[w2] = []
            try:
                dist = syns_shortest_path(w1,w2)
                if dist <= mindist:
                    sim_dict[w1].append(w2)
                    sim_dict[w2].append(w1)
            except:
                continue
        i += 1
    with open(simdict_file, "wb") as pf:
        pickle.dump(sim_dict, pf)


#compute shortest distance between two words in wordnet
def syns_shortest_path(w1, w2):
#collect all synsets for each word
    w1_syns =  wn.synsets(w1)
    w2_syns = wn.synsets(w2)
#take the minimum distance of all pairwise distances of w1 and w2 synsets -- distance = 0 means same synset
#only consider distances where w1 and w2 synsets have the same POS; discard wordnet distance errors (shortest_path_distance() = None)
    distance = min([i.shortest_path_distance(j) for i in w1_syns
                    for j in w2_syns if (i.pos() == j.pos()
                                        and i.shortest_path_distance(j) != None)])
    return distance
