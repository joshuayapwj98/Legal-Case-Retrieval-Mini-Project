from stack import Stack
import math
import heapq
import collections
import nltk
import numpy as np

import time

from nltk.stem.porter import PorterStemmer
from postings_reader import PostingsReader

nltk.download('wordnet')
nltk.download('stopwords')

from nltk.corpus import wordnet
from nltk.corpus import stopwords
from string import punctuation

class Posting:

    def __init__(self, context = "", occurrences = 0, postings = {}):
        self.context = context
        self.occurrences = occurrences
        self.postings = {}
        if self.occurrences != 0:
            self.parse_postings(postings)

    def parse_postings(self, postings):
        postings_list = postings.split(' ')
        last_doc_id = 0  # keep track of the last processed doc_id
        for posting in postings_list:
            parts = posting.split(':')
            doc_id_increment, weight = parts[0].split(',')
            doc_id = last_doc_id + int(doc_id_increment)
            positions = []
            last_position = 0
            for p in parts[1].split(','):
                position = last_position + int(p)
                positions.append(position)
                last_position = position
            self.postings[doc_id] = {'weight': float(weight), 'positions': positions}
            last_doc_id = doc_id  # update the last processed doc_id

class QueryParser:

    def __init__(self):
        # N represents the total number of articles in the dataset.
        self.N = 0
        self.K = 10
        self.doc_lengths = dict()
        self.postings_reader = PostingsReader()
        self.stemmer = PorterStemmer()
        self.term_weights_dict = collections.defaultdict()

    def process_query(self, query, K):
        self.K = K
        
        print("processing query...")
        self.doc_lengths = self.get_document("document.txt")

        if 'AND' in query[0]:
            results = self.process_boolean_query(query)
        else:
            normalization_query_vectors, top_documents = self.process_freetext_query(query)
            # TESTING
            # top_documents = []
            if len(query) > 1:
                other_relevant_docs = [doc_id for doc_id in query[1:]]
                for doc_id in other_relevant_docs:
                    top_documents.append(int(doc_id))
            # First optimization: Start of Pseudo Relevance Feedback (RF)
            new_query_vectors = self.rocchio(normalization_query_vectors, top_documents)
            top_term_vectors = self.get_top_K_word_vectors(new_query_vectors, 100)
            # new_query_terms = self.filter_relevant_words(self.tokenize_query(query[0]), top_term_vectors, False)
            
            # Second optimization: Perform filtering and query optimzation with WordNet
            # new_query_terms = self.filter_relevant_words(self.tokenize_query(query[0]), top_term_vectors)
            
            # Update query terms into normalization_query_vectors
            for term in top_term_vectors:
                normalization_query_vectors[term[1]] = term[0]

            # Create new revised query
            # revised_query = query[0]
            # for term in top_term_vectors:
            #     revised_query += ' ' + term[1]

            normalization_query_vectors, top_documents = self.process_freetext_query(query, normalization_query_vectors)
            results = top_documents

        return results


    # ==========================================================================
    # ====================== BOOLEAN QUERY PROCESSING ==========================
    # ==========================================================================
    '''
    Process query terms by smallest doc_freq first for optimisation. Queries could be 
    - "fertility treatment" AND "sus words" AND chicken AND nuggets
    - chicken AND nuggets 
    '''
    def process_boolean_query(self, query):
        print("processing boolean query...")

        # Split the query string into terms using 'AND' as the delimiter
        terms = query[0].split(' AND ')
        # print(terms)

        # 1. Go through the entire query and put it into a py dict.
        # Put phrasal queries in a separate dictionary, where the key is the phrasal query and the value is the postings list. 
        terms_postings_list = {} # Key: term, Value: postings list
        terms_doc_freq = {} # Key: term, Value: doc_freq
        
        # Process phrasal queries
        for t in terms:
            t = t.strip('"')
            postings_result_set = set()
            if self.is_phrase(t):
                phrasal_terms = self.tokenize_boolean_query(t) # Returns a list of up to 3 terms (phrase)
                # print(phrasal_terms)
                postings_result_set = self.process_phrase(phrasal_terms)
                # print("These are the results:", postings_result_set)
                
                # Add to temp dictionaries to do AND operations
                # print(t, postings_result_set)
                terms_postings_list[t] = postings_result_set
                terms_doc_freq[t] = len(postings_result_set)

            else: 
                # Put the term's doc_feq in the query_terms dict
                term = self.tokenize_boolean_query(t)
                postings_list = self.get_postings_list(term[0]).postings
                terms_postings_list[t] = set(postings_list.keys())
                terms_doc_freq[t] = len(set(postings_list.keys()))
        
        # print(terms_postings_list)
        # print(terms_doc_freq)

        # 2. Loop, maintaining a stack of size 2 to operate 'AND' on.
        self_combining_stack = Stack()
        while terms_doc_freq: 
            
            # 2a. Pop the smallest value in the dictionary, get the postings list of the key, and add it to the stack. 
            min_key = min(terms_doc_freq, key=terms_doc_freq.get)
            # print(min_key)
            postings_list = terms_postings_list[min_key]
            # print(postings_list)
            terms_doc_freq.pop(min_key)

            # 2b. Add to operator stack
            self_combining_stack.push(postings_list)
            
        common_docs = self_combining_stack.pop()
        return list(common_docs)

    # ======================================================================
    # ====================== FREE TEXT PROCESSING ==========================
    # ======================================================================
    '''
    Process queries that does not contain an 'AND' keyword. Queries could be
    - quiet phone call
    - good grades exchange scandal
    '''
    def process_freetext_query(self, query, normalization_query_vectors = []):
        # Collection to count the occurences of a term in a query
        query_count_dict = collections.defaultdict(lambda: 0)

        score_dict = collections.defaultdict(float)

        terms = self.tokenize_query(query[0])

        for term in terms:
            query_count_dict[term] += 1

        if len(normalization_query_vectors) == 0:
            # Get normalization query vectors
            normalization_query_vectors = self.get_query_normalization_vectors(query_count_dict)

        # Calculate the scores of each term w.r.t document
        for term in terms:
            w_tq = normalization_query_vectors[term]
            posting_obj = self.get_postings_list(term)
            
            postings_list = posting_obj.postings

            for document_id, props in postings_list.items():
                w_td = props['weight']

                score_dict[document_id] += w_tq * w_td
        
        # Normalize score with document length
        for document_id in score_dict:
            score_dict[document_id] /= self.doc_lengths[document_id]

        # Get top K documents
        top_documents = self.get_top_K_components(score_dict, self.K)

        return normalization_query_vectors, top_documents
    
    # ====================================================================
    # ====================== RANKING PROCESSING ==========================
    # ====================================================================
    
    def tokenize_boolean_query(self, terms):
        tokenized_terms = []

        for term in terms.split(' '):
            # stem and case-folding
            word_token = self.stemmer.stem(term).lower()
            if len(word_token) == 0:
                continue
            else: tokenized_terms.append(word_token)
        
        return tokenized_terms

    def tokenize_query(self, query):
        query = query.strip()
        terms = []

        for sentence_token in nltk.tokenize.sent_tokenize(query):
            for word_token in nltk.tokenize.word_tokenize(sentence_token):
                # stem and case-folding
                word_token = self.stemmer.stem(word_token).lower()
                if len(word_token) == 0:
                    continue
                else: terms.append(word_token)
                
        return terms
    
    def get_query_normalization_vectors(self, term_dict):
        square_w_tq_list = []
        query_weight_dict = collections.defaultdict(lambda: 0)
        norm_query_weight_dict = {key: 0 for key in term_dict.keys()}

        for term in term_dict:
            if term not in query_weight_dict:
                tf = idf = 0
                posting_obj = self.get_postings_list(term)
                occurrences = int(posting_obj.occurrences)

                tf = 1 + math.log(term_dict[term], 10)

                if occurrences != 0:
                    idf = math.log(self.N/occurrences, 10)
                
                w_tq = tf * idf
                query_weight_dict[term] = w_tq
                square_w_tq_list.append(w_tq ** 2)
        
        square_w_tq_list.sort()
        query_normalization_factor = math.sqrt(sum(square_w_tq_list))

        for term in term_dict:
            norm_query_weight_dict[term] = query_weight_dict[term] / query_normalization_factor
        
        return norm_query_weight_dict

    def get_top_K_word_vectors(self, scores_dic, K):
        result = []
        score_tuples = [(-score, doc_id) for doc_id, score in scores_dic.items()]
        
        heapq.heapify(score_tuples)

        for i in range(K):
            if len(score_tuples) != 0:
                tuple_result = heapq.heappop(score_tuples)
                result.append((abs(tuple_result[0]),) + tuple_result[1:])
            else:
                break

        return result
    
    def get_top_K_components(self, scores_dic, K):
        result = []
        score_tuples = [(-score, doc_id) for doc_id, score in scores_dic.items()]
        
        heapq.heapify(score_tuples)

        for i in range(K):
            if len(score_tuples) != 0:
                tuple_result = heapq.heappop(score_tuples)
                if tuple_result[1] not in result:
                    result.append(tuple_result[1])
            else:
                break

        return result
    
    # ===========================================================================
    # ====================== QUERY EXPANSION TECHNIQUE ==========================
    # ===========================================================================

    # def filter_relevant_words(self, query, terms, use_word_net = True):
    #     stop_words = set(stopwords.words('english'))
    #     punc = set(punctuation)
        
    #     filtered_words = [term for term in terms if term[1] not in stop_words \
    #                       and term[1] not in punc \
    #                         and term[1] not in query]
        
    #     if use_word_net == True:
    #         relevant_synonyms = self.word_net(query)
    #         filtered_words = [term for term in terms if term[1] in relevant_synonyms]
        
    #     return filtered_words

    def word_net(self, query):
        # Find synonyms for each word in the query
        synonyms = set()
        for word in query:
            for synset in wordnet.synsets(word):
                synonyms.update(synset.lemma_names())

        print("Synonyms:", synonyms)
        return synonyms

    def rocchio(self, normalized_query_vectors, relevant_docs, alpha=1, beta=0.70, gamma=0.05):
        docs_id_set = set()
        
        centroid_weights = collections.defaultdict(float)
        anti_centroid_weights = collections.defaultdict(float)
        query_centroid = collections.defaultdict(float)

        num_relevant_docs = len(relevant_docs)

        # Takes approx. 0.3 seconds for 10000+ dictionary terms
        term_weights_dict = self.get_all_doc_weights()

        # Find the weights of the the terms inside the relevant documents
        for term, posting in term_weights_dict.items():
            # postings_dict is a dictionary that has the doc_id as key and an object containing the weight and positions
            # Example for the word 'inform':
            # 1. '12323': {'weight': 1.2323, 'positions': [12, 356, 2234]}
            postings_dict = posting.postings
            for doc_id, props in postings_dict.items():
                weight = props['weight']
                # Add to set of document collection
                if doc_id not in docs_id_set:
                    docs_id_set.add(doc_id)

                if doc_id in relevant_docs:
                    # Add to relevant centroid weights
                    centroid_weights[term] += weight
                else: 
                    # Add to non-relevant centroid weights
                    anti_centroid_weights[term] += weight

        # Calculate the average weight of the a term across all relevant documents 
        for term in centroid_weights:
            centroid_weights[term] /= num_relevant_docs
        
        # Calculate the average weight of the a term across all non relevant documents 
        for term in anti_centroid_weights:
            anti_centroid_weights[term] /= (len(docs_id_set) - num_relevant_docs)   

        # Calculate the Rocchio algorithm
        for term, weight in normalized_query_vectors.items():
            query_centroid[term] = alpha * weight

        for term, weight in centroid_weights.items():
            query_centroid[term] += beta * weight

        for term, weight in anti_centroid_weights.items():
            query_centroid[term] -= gamma * weight

        return query_centroid

    # ==========================================================================
    # ====================== PHRASAL QUERY PROCESSING ==========================
    # ==========================================================================
    '''
    Processes the phrasal query and returns a list of documents that are
    relevant.  
    '''
    def process_phrase(self, phrase):
        postings_dict = {}
        postings = []

        # 1. Obtain the postings for each term
        for term in phrase:
            posting = self.get_postings_list(term)
            if len(posting.postings) != 0:
                postings_map = posting.postings
                postings_dict[term] = postings_map
                postings.append(set(postings_map.keys()))
            else:
                # postings.append(set())
                # TODO: Check if returning an empty list since a term is not present in any document
                return set()
        
        # 2. Find the common documents from the set of document IDs
        common_docs = postings[0]
        for i in range(1, len(postings)):
            common_docs = common_docs & postings[i]

        valid_docs = set()
        # 3. For each common document, check document(s) for the term sequence
        for doc in common_docs:
            
            is_valid = True

            for i in range(0, len(phrase) - 1):
                positions1 = postings_dict[phrase[i]][doc]['positions']
                positions2 = postings_dict[phrase[i+1]][doc]['positions']
                is_consecutive = self.check_consecutive(positions1, positions2)
                if is_consecutive == False:
                    is_valid = False
                    break

            if is_valid == True:
                valid_docs.add(doc)
            
        return valid_docs
    
    def check_consecutive(self, arr1, arr2):
        arr1_set = set(arr1)
        # O(n) time complexity
        for num in arr2:
            if num - 1 in arr1_set:
                return True
        return False

    def is_phrase(self, string): 
        return string.count(' ') > 0

    # ==========================================================================
    # ====================== ACCESS INDEXING ===================================
    # ==========================================================================

    def get_all_doc_weights(self):
        doc_weights_dic = collections.defaultdict()
        with open('Postings.txt', 'r') as f:
            for line in f:
                line = line.strip()
                context, occurrences, postings = line.split(' ', 2)
                posting = Posting(context, occurrences, postings)
                doc_weights_dic[context] = posting
        
        return doc_weights_dic

    def get_postings_list(self, term):
        postings_list_ptr = self.postings_reader.get_postings_ptr(term)
        with open('postings.txt', 'r') as f:
            if postings_list_ptr == -1:
                # print('[DEBUG] Cannot find term', term)
                posting = Posting(term)
            else:
                # print('[DEBUG] Found term', term)
                line = f.seek(postings_list_ptr, 0)
                line = f.readline().strip()
                context, occurrences, postings = line.split(' ', 2)

                # Create a new Posting instance
                posting = Posting(context, occurrences, postings)
                # Postings.postings variable example: [{'doc_id': 246391, 'weight': 1.0, 'positions': [6]}, {'doc_id': 9, 'weight': 1.0, 'positions': [0]}]
            return posting
    
    def get_document(self, file_name):
        doc_length = dict()
        with open(file_name, 'r') as f:
            data = f.read().split()
            # Set N as the total number of articles
            self.N = int(data[0])
            # Iterate through each document pair
            for docid_length in data[1:]:
                docid_length = docid_length.split(',')
                document_id = int(docid_length[0])
                document_length = float(docid_length[1])
                doc_length[document_id] = document_length
            
        return doc_length

