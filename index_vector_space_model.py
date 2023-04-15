import os
import sys
import csv
import math
import time
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem.porter import PorterStemmer

class VectorSpaceModel:
    """
    Class that construct and write data from in_dir into out_dict, out_postings, all_doc_ids.txt and document.txt files

    in_dir: input directory containing all documents for indexing
    out_dict: output file written in the form of [term doc_freq posting_ref]
    out_postings: output file written in the form of [term (docID, w-tf) (docID, w-tf) ...], 
                    where w-tf = (1 + log(tf)), 
                    where tf is the term frequency of the term t in docID
    all_doc_ids.txt: output file containing the ID of all documents, separated by a single space
    document.txt: output file written in the form of [total_num_of_doc (docID, len_of_doc) (docID, len_of_doc) ...],
                    where len_of_doc is the length of the document in vector space 
    """

    MAX_LINES_IN_MEM = 10000

    def __init__(self, in_dir, out_dict, out_postings):
        """
        Initialise input directory and output files
        """
        print("initialising vector space model...")

        self.in_dir = in_dir
        self.out_dict = out_dict
        self.out_postings = out_postings
    
    def parse_data(self):
        """
        

            Returns:
                
        """
        total_docs = -1
        # max_docs = float('inf')
        max_docs = 500

        all_doc = {}
        all_doc_ids = []
        title = {}
        content = {}
        date_posted = {}
        court = {}

        csv.field_size_limit(sys.maxsize)

        with open(self.in_dir, 'r') as file:
            reader = csv.reader(file, delimiter = ',')
            for data in reader:
                total_docs += 1
                # skip column titles
                if (total_docs == 0):
                    continue
                if (total_docs > max_docs):
                    break
                if data[0] in all_doc:
                    prev_data = all_doc[data[0]]
                    prev_data[0] += " " + data[1]
                    prev_data[1] += " " + data[2]
                    prev_data[2] += " " + data[3]
                    prev_data[3] += " " + data[4]
                    all_doc[data[0]] = prev_data
                else:
                    all_doc[data[0]] = data[1:]

        # sort data in increasing doc_id
        dict(sorted(all_doc.items()))

        for key in all_doc:
            all_doc_ids.append(key)
            title[key] = all_doc[key][0]
            content[key] = all_doc[key][1]
            date_posted[key] = all_doc[key][2]
            court[key] = all_doc[key][3]

        # Write to a txt file for search to access all doc_ids 
        with open("all_doc_ids.txt", "w") as file:
            file.write(" ".join(map(str, all_doc_ids)))

        print("completed parsing {} number of data".format(len(all_doc)))

        return all_doc_ids, title, content, date_posted, court
    
    def reset_files(self):
        """
        Method to delete all files generated from the previous indexing
        """
        print("deleting previous test files...")
        if os.path.exists(self.out_postings):
            os.remove(self.out_postings)

        if os.path.exists(self.out_dict):
            os.remove(self.out_dict)

        if os.path.exists("all_doc_ids.txt"):
            os.remove("all_doc_ids.txt")

        if os.path.exists("document.txt"):
            os.remove("document.txt")

        if os.path.exists("pointers.txt"):
            os.remove("pointers.txt")
        
    def construct(self):
        """
        Method to construct the indexing of all terms and their postings
        """
        st = time.time()
        self.reset_files()

        print("constructing index...")
        stemmer = PorterStemmer()
        all_doc_ids, title, content, date_posted, court = self.parse_data()
        total_num_docs = len(all_doc_ids)
        terms = list() # a list of terms
        term_doc_freq = {} # key: string, value: int { term : doc_freq }
        term_id_pos = {} # { term : { docID : [position...] } }
        postings = {} # key: string, value: a dictionary { term : {docID : term_freq, docID : term_freq ...} }
        count = 0

        for doc_id in all_doc_ids:
            if (count % 100 == 0):
                print("completed parsing {} number of documents. Parsing next 100 documents...".format(count))
                end = time.time()
                print("time taken: " + str(end - st))

            doc_id = str(doc_id)
            terms_counted = list() # list of terms in doc_id already counted in doc_freq
            position = 0 # positional index
            doc_content = content[doc_id].split("\n")
            for line in doc_content:
                for sentence_token in sent_tokenize(line):
                    for word_token in word_tokenize(sentence_token):
                        # stem and case-folding
                        word_token = stemmer.stem(word_token).lower()
                        # skip empty strings
                        if len(word_token) == 0:
                            continue
                        else:
                            # first unique instance of term in all docs
                            # add word_token into list of terms
                            if word_token not in terms:
                                terms.append(word_token)
                                term_doc_freq[word_token] = 1 # { term : doc_freq }
                                terms_counted.append(word_token)

                            # check if doc_id is counted in doc_freq
                            if word_token not in terms_counted:
                                term_doc_freq[word_token] += 1 # { term : doc_freq }
                                terms_counted.append(word_token)
                            
                            # add word_token into posting list
                            # value as { term : docID : [position...]}
                            if word_token not in term_id_pos:
                                term_id_pos[word_token] = {}
                                term_id_pos[word_token][doc_id] = list()
                                term_id_pos[word_token][doc_id].append(position)
                            else :
                                if doc_id not in term_id_pos[word_token]:
                                    term_id_pos[word_token][doc_id] = list()
                                    term_id_pos[word_token][doc_id].append(position)
                                else:
                                    term_id_pos[word_token][doc_id].append(position)
                            position += 1
            count += 1
        
        doc_len, postings = self.construct_weighted_postings(all_doc_ids, term_id_pos)
        terms.sort()
        self.write_output_files(terms, term_doc_freq, postings)
        self.write_output_document(total_num_docs, doc_len)

    def construct_weighted_postings(self, all_doc_ids, term_id_pos):
        """
        Method to calculate weighted = 1 + log(term_frequency)
        Replace term_freq to weighted in postings, and get the length of each document and store in doc_len

            Parameter:
                postings: a dictionary with string as key and dictionary as value, { term : {docID : term_freq, docID : term_freq ...} }
            
            Returns:
                doc_len and updated postings
        """
        doc_len = {} # { docID : doc_len, docID : doc_len ... }
        postings = {} # { term : (docID,weightedtf) : [position...] }

        # initialise all doc length to 0
        for doc_id in all_doc_ids:
            doc_len[doc_id] = 0 

        # normalise term frequency for each document
        for term in term_id_pos: # { term : docID : [position...]}

            for doc_id in term_id_pos[term]:
                term_freq = len(term_id_pos[term][doc_id])
                log_term_freq_weighted = 1 + math.log(term_freq, 10)
                # term_id_pos[term][doc_id] = log_term_freq_weighted # value as { docID : log_term_freq_weighted ... }

                if term not in postings:
                    postings[term] = {}

                docID_weight = (doc_id, log_term_freq_weighted)

                # { term : (docID,weight) : [position...] }
                postings[term][docID_weight] = term_id_pos[term][doc_id]

                doc_len[doc_id] += log_term_freq_weighted * log_term_freq_weighted
                
        for doc_id in doc_len:
            doc_len[doc_id] = math.sqrt(doc_len[doc_id]) # { docID : doc_len, docID : doc_len ... }
        
        return doc_len, postings

    def write_output_files(self, terms, term_doc_freq, postings):
        """
        Method to write into out_dict, out_postings and document.txt

            Parameters:
                terms: a list of string, sorted in ascending alphanumeric order
                term_doc_freq: a dictionary with string as key and int as value, { term : doc_freq }
                postings: a dictionary with string as key and dictionary as value, { term : {docID : term_freq, docID : term_freq ...} }
                doc_len: a dictionary with string as key and int as value, { docID : doc_len, docID : doc_len ... }
                total_num_docs: an int representing the total number of documents
                
        """
        print("preapring content for dictionary, postings and documents output files...")

        final_dictionary = "" # term doc_freq reference
        final_postings = "" # term (docID,term_freq) (docID,term_freq) ...
        final_pointers = "" # (dict_ptr,posting_ptr,posting_ptr,posting_ptr,posting_ptr) ...
        posting_ref = 0
        dictionary_ref = 0
        line_in_mem = 0
        block_size = 4 # index compression blocking
        posting_pointer = list()

        for term in terms:
            # postings = { term : { (docID,weightedtf) : [position...] } }

            posting = postings[term] # { (docID,weightedtf) : [position...] }
            doc_freq = str(term_doc_freq[term]) # { term : doc_freq }
            posting_content = ""
            dictionary_content = ""
            dict_post_pointer = ""
            prev_id = 0

            for docID_weighted, positions in posting.items():
                doc_id = int(docID_weighted[0])
                gap_encoded_id = doc_id - prev_id
                weightedtf = str(docID_weighted[1])
                position = ','.join(str(e) for e in positions)

                posting_content += " {},{}:{}".format(gap_encoded_id, weightedtf, position)

                prev_id = doc_id

            new_posting = "{} {}{}\n".format(term, doc_freq, posting_content)

            posting_pointer.append(posting_ref)
            posting_ref += len(new_posting)
            final_postings += new_posting

            if (len(posting_pointer) < block_size):
                dictionary_content = "|{}|{}".format(str(len(term)), term)
                final_dictionary += dictionary_content
            else:
                dictionary_content = "|{}|{}".format(str(len(term)), term)
                final_dictionary += dictionary_content

                posting_ref_content = ','.join(str(e) for e in posting_pointer)
                dict_post_pointer = " {},{}".format(dictionary_ref, posting_ref_content)
                dictionary_ref += len(dict_post_pointer)
                final_pointers += dict_post_pointer
                posting_pointer = list()
            
            # write out into dictionary and postings files
            if (line_in_mem == self.MAX_LINES_IN_MEM):
                print("append next 100 terms into dictionary, posting and pointers.txt files")
                self.append_content(self.out_dict, final_dictionary)
                self.append_content(self.out_postings, final_postings)
                self.append_content("pointers.txt", final_pointers)

                # reset values
                line_in_mem = 0
                final_dictionary = "" 
                final_postings = ""
                final_pointers = ""
        
            line_in_mem += 1
        
        if (len(posting_pointer) != 0):
            posting_ref_content = ','.join(str(e) for e in posting_pointer)
            dict_post_pointer = " {},{}".format(dictionary_ref, posting_ref_content)
            dictionary_ref = len(final_dictionary)
            final_pointers += dict_post_pointer
            posting_pointer = list()

        # write out into final dictionary, postings and pointers files
        print("writing to output files...")
        self.append_content(self.out_dict, final_dictionary)
        self.append_content(self.out_postings, final_postings)
        self.append_content("pointers.txt", final_pointers)

    def write_output_document(self, total_num_docs, doc_len):
        final_document = "" # totalNumDocs (docID,lenOfDoc) (docID,lenOfDoc) ...
        final_document += str(total_num_docs)

        for doc_id in doc_len:
            final_document += " {},{}".format(str(doc_id), str(doc_len[doc_id]))

        # write out into final document file
        print("writing to document.txt file")
        self.write_content("document.txt", final_document)
        
    def write_content(self, out_file, content):
        """
        Method to write content into file
        
            Parameters:
                out_file: a file
                content: a string
        """
        f = open(out_file, "w")
        f.write(content)
        f.close()

    def append_content(self, out_file, content):
        """
        Method to write content into file
        
            Parameters:
                out_file: a file
                content: a string
        """
        f = open(out_file, "a")
        f.write(content)
        f.close()

