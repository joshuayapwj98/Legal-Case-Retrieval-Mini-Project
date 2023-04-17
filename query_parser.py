from stack import Stack
import math
import heapq
import collections
import nltk

from nltk.stem.porter import PorterStemmer
from postings_reader import PostingsReader

class Posting:

    def __init__(self, context, occurrences, postings):
        self.context = context
        self.occurrences = occurrences
        self.postings = {}
        self.parse_postings(postings)

    def parse_postings(self, postings):
        postings_list = postings.split(' ')
        last_doc_id = 0  # keep track of the last processed doc_id
        for posting in postings_list:
            parts = posting.split(':')
            doc_id_increment, weight = parts[0].split(',')
            doc_id = last_doc_id + int(doc_id_increment)
            self.postings[doc_id] = float(weight)
            last_doc_id = doc_id  # update the last processed doc_id

class QueryParser:

    def __init__(self):
        # N represents the total number of articles in the dataset.
        self.N = 0
        self.K = 10
        self.doc_lengths = dict()
        self.postings_reader = PostingsReader()
        self.stemmer = PorterStemmer()

    def process_query(self, query, K):
        self.K = K
        
        print("processing query...")
        self.doc_lengths = self.get_document("document.txt")

        if 'AND' in query[0]:
            results = self.process_boolean_query(query)
        else:
            results = self.process_freetext_query(query)

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

        # 1. Go through the entire query and put it into a py dict.
        # Put phrasal queries in a separate dictionary, where the key is the phrasal query and the value is the postings list. 
        phrasal_terms = {} # Key: term, Value: postings list
        query_terms = {} # Key: term, Value: doc_freq
        
        # Process phrasal queries
        for t in terms:
            t = t.strip('"')
            if self.is_phrase(t):
                postings_result = self.process_phrase(t)
                phrasal_terms[t] = postings_result
                # query_terms[t] = postings_result.count() --> len of docIDs

            else: 
                # Put the term's doc_feq in the query_terms dict
                pass

        
        # 2. Loop, maintaining a stack of size 2 to operate 'AND' on.
        self_combining_stack = Stack()
        while query_terms: 
            
            # 2a. Pop the smallest value in the dictionary, get the postings list of the key, and add it to the stack. 
            min_key = min(query_terms, key=query_terms.get)
            postings_list = self.get_postings_list(min_key)

            # 2b. Add to operator stack
            self_combining_stack.push(postings_list)
            
        common_docs = []
        if not self_combining_stack.isEmpty():
            common_docs.append(self_combining_stack.pop())

        return common_docs
    

    # ======================================================================
    # ====================== FREE TEXT PROCESSING ==========================
    # ======================================================================
    '''
    Process queries that does not contain an 'AND' keyword. Queries could be
    - quiet phone call
    - good grades exchange scandal
    '''
    def process_freetext_query(self, query):
        # Collection to count the occurences of a term in a query
        query_count_dict = collections.defaultdict(lambda: 0)

        score_dict = collections.defaultdict(float)

        # # Iterate through each term in the contextual query
        # q = query[0]
        # words = re.findall(r'(\w+|"[^"]+")', q)

        # # Remove the quotes from the words in double quotes
        # words = [word.strip('"') for word in words]

        terms = self.tokenize_query(query[0])


        for term in terms:
            query_count_dict[term] += 1

        normalization_query_vectors = self.get_query_normalization_vectors(query_count_dict)

        for term in terms:
            w_tq = normalization_query_vectors[term]
            posting_obj = self.get_postings_list(term)
            postings_list = posting_obj.postings

            for document_id in postings_list.keys():
                w_td = postings_list[document_id]

                score_dict[document_id] += w_tq * w_td
        
        for document_id in score_dict:
            score_dict[document_id] /= self.doc_lengths[document_id]

        return self.get_top_K_components(score_dict, self.K)
    
    # ====================================================================
    # ====================== RANKING PROCESSING ==========================
    # ====================================================================
    
    def tokenize_query(self, query):
        query = nltk.tokenize.word_tokenize(query.strip())
        terms = []

        for term in query:
            stemmed = self.stemmer.stem(term.lower())
            terms.append(stemmed)
        
        return terms

    def get_query_term_weight(self, query_term, termIndex, postings_list_len):
        if postings_list_len == 0:
            return 0
        return (1 + math.log(termIndex[query_term], 10)) * math.log(self.N/postings_list_len, 10)

    def get_document_term_weight(self, document_term_frequency):
        return 1 + math.log(document_term_frequency, 10)

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

    def get_top_K_components(self, scores_dic, K):
        result = []
        score_tuples = [(-score, doc_id) for doc_id, score in scores_dic.items()]
        
        heapq.heapify(score_tuples)

        for i in range(K):
            if len(score_tuples) != 0:
                tuple_result = heapq.heappop(score_tuples)
                result.append(tuple_result[1])
            else:
                break

        return result

    # ==========================================================================
    # ====================== PHRASAL QUERY PROCESSING ==========================
    # ==========================================================================
    '''
    Processes the phrasal query and returns a list of documents that are
    relevant.  
    '''
    def process_phrase(self, phrase):
        return

    def is_phrase(self, string): 
        return string.count(' ') > 0

    # ==========================================================================
    # ====================== ACCESS INDEXING ===================================
    # ==========================================================================

    def get_postings_list(self, term):
        stemmed_token = self.stemmer.stem(term).lower()
        postings_list_ptr = self.postings_reader.get_postings_ptr(stemmed_token)
        with open('postings.txt', 'r') as f:
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

