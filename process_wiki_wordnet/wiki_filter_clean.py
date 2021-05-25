import boto3
import re
import os
import pickle
import numpy as np
from nltk.corpus import wordnet as wn

#create connection to s3 bucket using stored IAM credentials
s3 = boto3.resource('s3', region_name='us-east-1')

#calculate term frequencies for all whole wiki dump, create list of top 30K (or 90% for short documents) most frequent words
def find_top_wiki(bucket,text_file,s3,wiki_words_file):
    print("finding top words")
    word_dict = dict()    
    wl = set(wn.words())
    print("counting words")
    line_num = 0
    with open(text_file, "r") as zf:
        for line in zf:
            if line_num % 1000000 == 0:
                print("reading line: ", line_num)
            line_num += 1
            words =line.lower().split(" ")
            for word in words:
                if word in word_dict:
                    word_dict[word] += 1
#only include words that are in wordnet
                elif word in wl:
                    word_dict[word] = 1
    with  open("word_dict.pkl", "wb") as pickle_dict:
        pickle.dump(word_dict ,pickle_dict)
    if len(word_dict) > 30000:
        length = 29999
    else:
        length = len(word_dict) - round((len(word_dict)*0.1),0)
    print("sorting words")
    top30K_words = []
    top30K_counts = []
    min_loc = 0
    min_count = 0
#find top |length| words without processing entire dictionary in memory
    for i, word in enumerate(word_dict):
        if i == 0:
            min_count = word_dict[word]
        if len(top30K_words) < length:
            if word_dict[word] < min_count:
                min_count = word_dict[word]
                min_loc = i
            top30K_words.append(word)
            top30K_counts.append(word_dict[word])    
        else:
            if word_dict[word] > min_count:
                top30K_words[min_loc] = word
                top30K_counts[min_loc] = word_dict[word]
                min_count = min(top30K_counts)
                min_loc = np.argmin(top30K_counts)
    print("writing word list")
#save word list locally and upload to s3
    with open(wiki_words_file, "w", encoding = "utf-8") as wf:
        for word in top30K_words:
            row = word +"\n"
            wf.write(row)
    s3.meta.client.upload_file(wiki_words_file, bucket, wiki_words_file)
    return set(top30K_words)

#iterate through wiki dump and remove any words not in the top 30K word list
def clean_wiki_file(bucket, text_file, s3, wiki_words, clean_file):
    print("cleaning wiki text")
    line_num = 0
#save cleaned text locally and upload to s3
    with open(text_file, "r") as rf:
        with open(clean_file, "w") as wf:
            for line in rf:
                if line_num % 1000000 == 0:
                    print("cleaning line: ", line_num)
                line_num += 1
                words = line.lower().split(" ")
                row = ' '.join([w for w in words if (w in wiki_words and w != '\n')]) + '\n'
                wf.write(row)
        s3.meta.client.upload_file(clean_file, bucket, clean_file)
    
def wiki_filter_clean(bucket, s3,text_file, wiki_words_file, clean_file):
    wiki_words = find_top_wiki(bucket,text_file,s3,wiki_words_file)
    clean_wiki_file(bucket, text_file, s3, wiki_words, clean_file)

