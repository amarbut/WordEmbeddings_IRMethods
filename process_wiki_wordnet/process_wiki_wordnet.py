from clean_wiki_text import *
from wiki_filter_clean import *
from wordnet_simdict import *
import boto3

#connect to s3 using stored credentials
s3 = boto3.resource('s3', region_name='us-east-1')

#unzip and clean wiki dump, compute top 30K words and filter wiki text, create wordnet similarity dictionary for word list
def process_wiki_wordnet(index_file, bz2_file, unzip_file, s3, bucket, wordlist_file, clean_file, mindist, simdict_file):
    index_bytes = make_wiki_byte_index(index_file, bz2_file)
    compile_wiki_text(index_bytes, bz2_file, unzip_file)
    wiki_filter_clean(bucket, s3, unzip_file, wordlist_file, clean_file)
    wordnet_simdict(wordlist_file, mindist, simdict_file)

if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--index_file', help = 'byte index for bz2 file', required = True)
    parser.add_argument('--bz2_file', help = 'bz2 file with text data', required = True)
    parser.add_argument('--unzip_file', help = 'file location for uncompressed bz2 text', required = True)
    parser.add_argument('--bucket', help = 's3 bucket for project', required = True)
    parser.add_argument('--word_list_file', help='file location for word list', required=True)
    parser.add_argument('--clean_file', help = 'file location for cleaned text', required = True)
    parser.add_argument('--mindist', help = 'number of wordnet nodes to consider similar', required = True)
    parser.add_argument('--simdict_file', help = 'file location to dump similarity dict', required = True)
    args = parser.parse_args()
    process_wiki_wordnet(args.index_file, args.bz2_file, args.unzip_file, s3, args.bucket, 
                         args.word_list_file, args.clean_file, args.mindist, args.simdict_file) 
