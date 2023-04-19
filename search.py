#!/usr/bin/python3
import os
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import sys
import getopt
from query_parser import QueryParser

# python3 search.py -d dictionary.txt -p postings.txt -q queries.txt -o results.txt


def usage():
    print("usage: " +
          sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


def run_search(dict_file, postings_file, queries_path, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    # This is an empty method
    # Pls implement your code in below
    
    parser = QueryParser()
    inFiles = os.listdir(queries_path)
    sorted_files = sorted(inFiles)

    # Iterate through all the files in the queries folder
    for file_name in sorted_files:
        # if count == 0: break
        file_path = os.path.join(queries_path, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                # Get the contents of the text file and split it by the break line
                contents = file.read().split('\n')
                result = parser.process_query(contents, 10)
                result_string = ', '.join(map(str, result))
                print(result_string)
                # print('result for', file_name, result)
                

dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
