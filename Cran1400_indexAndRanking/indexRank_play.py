# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 10:41:43 2021

@author: Anna
"""

#import ir_datasets
import string
from nltk.corpus import stopwords
import numpy as np

# train = ir_datasets.load('msmarco-passage/train/split200-train')
# test = ir_datasets.load('msmarco-passage/train/split200-valid')

term_index = dict()
punct = str.maketrans('','',string.punctuation)
stop = set(stopwords.words('english'))
#to make sure the document parsing doesn't skip anyone
docs_check = set()
lengths = []

#process documents and create inverted index
with open("cran.tar/cran.all.1400", "r", encoding = "utf-8") as file:
    line = file.readline()
    split_line = line.split() 
    while len(split_line) > 0:
        if split_line[0] == '.I':
            doc_id = split_line[1]
            docs_check.add(doc_id)
            line = file.readline()
            split_line = line.split() 
        elif split_line[0] == '.W':
            text = []
            line = file.readline()
            split_line = line.split()
            stripped = [w.translate(punct).lower() for w in split_line if w not in stop]
            while len(split_line) > 0 and  split_line[0] != '.I':
                text.extend(stripped)
                line = file.readline()
                split_line = line.split()
                stripped = [w.translate(punct).lower() for w in split_line if w not in stop]
            length = len(text)
            lengths.append(length)
            doc_terms = dict()
            for w in text:
                if w in doc_terms:
                    doc_terms[w] += 1
                else: 
                    doc_terms[w] = 1
            for w in doc_terms:
                #add doc_id, raw term count, normalized term frequency, and doc length to postings list entry
                meta = (doc_id, doc_terms[w], doc_terms[w]/length, length)
                if w in term_index:
                    term_index[w].append(meta)
                else:
                    term_index[w]=[meta]
        else:
            line = file.readline()
            split_line = line.split()
            
#calculate idf scores for each term
idf_index = dict()
for w in term_index:
    docs = len(term_index[w])
    idf_index[w] = np.log(1400/docs)

#create bag-of-word vectors for each query           
queries = dict()
i=1     
with open("cran.tar/cran.qry", "r", encoding = "utf-8") as file:
    line = file.readline()
    split_line = line.split()
    while len(split_line) > 0:
        if split_line[0] == '.I':
            q_id = i
            line = file.readline()
            split_line = line.split()
            i+= 1
        elif split_line[0] == '.W':
            text = []
            line = file.readline()
            split_line = line.split()
            stripped = [w.translate(punct).lower() for w in split_line if w not in stop]
            while len(split_line) >0 and split_line[0] != '.I':
                text.extend(stripped)
                line = file.readline()
                split_line = line.split()
                stripped = [w.translate(punct).lower() for w in split_line if w not in stop]
            queries[q_id] = text
        else:
            line = file.readline()
            split_line = line.split()

#create dict for relevance judgments
query_rel = dict()

with open("cran.tar/cranqrel", "r", encoding = "utf-8") as file:
    for line in file.readlines():
        q_id, doc_id, rel = line.split()
        q_id = int(q_id)
        if q_id in query_rel:
            query_rel[q_id].append(doc_id)
        else:
            query_rel[q_id] = [doc_id]

#calculate scores with  term frequency, boolean term presence, tfidf, rsv, and bm25
tf_rc_scores = []
tf_p_scores = []
tc_rc_scores = []
tc_p_scores = []
tfidf_rc_scores = []
tfidf_p_scores = []
rsv_rc_scores = []
rsv_p_scores = []
bm25_rc_scores = []
bm25_p_scores = []

#set bm25 params according to Manning's default recommendations
k1 = .9
b = .75
lavg = np.mean(lengths)
            
for q in queries:
    total_rel = len(query_rel[q])
    tfidf_score = dict()
    tf_score = dict()
    tc_score = dict()
    rsv_score = dict()
    bm25_score = dict()
    for t in queries[q]:
        if t in term_index:
            rt = np.sum([1 for i in query_rel[q] if i in [j[0] for j in term_index[t]]])
            pt = (rt/total_rel)
            idf = idf_index[t]
            for meta in term_index[t]:
                doc, tc, tf, length = meta
                if doc in tf_score:
                    tf_score[doc] += tf
                    tc_score[doc] += 1
                    tfidf_score[doc] += (tf*idf)
                    rsv_score[doc] += np.log(pt/(1-pt))+idf
                    bm25_score[doc] += idf*(k1+1)*tc/(k1*((1-b)+(b*(length/lavg)))+tc)
                    
                else:
                    tf_score[doc] = tf
                    tc_score[doc] = 1
                    tfidf_score[doc] = (tf*idf)
                    rsv_score[doc] = np.log(pt/(1-pt))+idf
                    bm25_score[doc] = idf*(k1+1)*tc/(k1*((1-b)+(b*(length/lavg)))+tc)
    
    #take top K docs according to each scoring method
    tf_ranks = sorted(tf_score, key = tf_score.get, reverse = True)[0:15]
    tc_ranks = sorted(tf_score, key = tc_score.get, reverse = True)[0:15]
    tfidf_ranks = sorted(tf_score, key = tfidf_score.get, reverse = True)[0:15]
    rsv_ranks = sorted(tf_score, key = rsv_score.get, reverse = True)[0:15]
    bm25_ranks = sorted(tf_score, key = bm25_score.get, reverse = True)[0:15]
    
    #create recall and precision scores for each scoring method
    tf_rc_scores.append(np.sum([1 for i in query_rel[q] if i in tf_ranks])/total_rel)
    tf_p_scores.append(np.sum([1 for i in query_rel[q] if i in tf_ranks])/len(tf_ranks))
    tc_rc_scores.append(np.sum([1 for i in query_rel[q] if i in tc_ranks])/total_rel)
    tc_p_scores.append(np.sum([1 for i in query_rel[q] if i in tc_ranks])/len(tf_ranks))
    tfidf_rc_scores.append(np.sum([1 for i in query_rel[q] if i in tfidf_ranks])/total_rel)
    tfidf_p_scores.append(np.sum([1 for i in query_rel[q] if i in tfidf_ranks])/len(tf_ranks))
    rsv_rc_scores.append(np.sum([1 for i in query_rel[q] if i in rsv_ranks])/total_rel)
    rsv_p_scores.append(np.sum([1 for i in query_rel[q] if i in rsv_ranks])/len(tf_ranks))
    bm25_rc_scores.append(np.sum([1 for i in query_rel[q] if i in bm25_ranks])/total_rel)
    bm25_p_scores.append(np.sum([1 for i in query_rel[q] if i in bm25_ranks])/len(tf_ranks))

#                       #k=15           #k=25
np.mean(tf_rc_scores)   #.296           #.362
np.mean(tf_p_scores)    #.135           #.103
np.mean(tc_rc_scores)   #.347           #.418
np.mean(tc_p_scores)    #.162           #.121
np.mean(tfidf_rc_scores)#.405           #.479
np.mean(tfidf_p_scores) #.190           #.138
np.mean(rsv_rc_scores)  #.081           #.118
np.mean(rsv_p_scores)   #.036           #.033
np.mean(bm25_rc_scores) #.474###        #.535###
np.mean(bm25_p_scores)  #.224###        #.156###

