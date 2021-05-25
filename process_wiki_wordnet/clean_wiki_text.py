import re
import bz2
from bs4 import BeautifulSoup
import os

#pull text out of xml, remove punctuation and extra whitespace
def clean_wiki_text(pages):
    text = []
    for p in pages:
        t = p.find("text").text
        clean = re.sub("['\",\\/;:()\[\]]", " ", re.sub("[\.!\?]", "\n" ,t.strip())).strip()
        text.append(clean)
    combined = " ".join(text)
    return(combined)
 
#used code from this blog to read bz2 multistream: https://data-and-the-world.onrender.com/posts/read-wikipedia-dump/
#create list of byte indices to pull each "stream" out of the .bz2 multistream file downloaded from wikidumps
def make_wiki_byte_index(index_file, read_file):
    print("creating bz2 file byte index")
    with bz2.open(index_file, "rb") as f:
        start_bytes = []
        for line in f:
            start = int(line.split(b":")[0])
            start_bytes.append(start)
        start_bytes = set(start_bytes)  ## to deduplicate the list
        start_bytes = list(start_bytes)  ## but we want them in a specific order
        start_bytes.sort()
    file_size = os.path.getsize(read_file)
    if (file_size - start_bytes[-1]) < 2000000:
        start_bytes.append(file_size + 1)
    return(start_bytes)

#iterate through byte indices, unzip and clean text, combine into single text file 
def compile_wiki_text(index_bytes, read_file, write_file):
    i = 0
    with open(write_file, "w") as wf:
        for eb in index_bytes:
            if i == 0:
                i += 1
            else:
                print("unzipping and cleaning chunk: ", i)
                sb = index_bytes[i-1]
                i += 1
                dc = bz2.BZ2Decompressor()
                with open(read_file, 'rb') as rf:
                    rf.seek(sb)
                    readback = rf.read(eb-sb-1)
                    page_xml = dc.decompress(readback).decode()
                soup = BeautifulSoup(page_xml, "lxml")
                pages = soup.find_all("page")
                text = clean_wiki_text(pages) 
                row = text + "\n"
                wf.write(row)
