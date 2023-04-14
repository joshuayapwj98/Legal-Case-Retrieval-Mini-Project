from stack import Stack
import math
import heapq
import collections

class QueryParser:

    def __init__(self):
        # N represents the total number of articles in the dataset.
        N = 0
        K = 10

    def process_query(self, query):

        print("processing query...")

        with open('document.txt', 'r') as f:
            data = f.read().split()
            # Set N as the total number of articles
            N = int(data[0])
            doc_lengths = [(int(data[i]), float(data[i+1])) for i in range(1, len(data), 2)]


        if 'AND' in query:
            results = self.process_boolean_query(query)
        else:
            results = self.process_freetext_query(query)


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
        terms = query.split(' AND ')
        print(terms)

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

        common_docs = self_combining_stack.pop()
        return common_docs

    def is_phrase(self, string): 
        return string.count(' ') > 0
    

    # ======================================================================
    # ====================== FREE TEXT PROCESSING ==========================
    # ======================================================================

    def process_freetext_query(self, query):
        # Collection to count the occurences of a term in a query
        queryIndex = collections.defaultdict(lambda: 0)
        # Collection to store the query term weight
        query_weight_dict = collections.defaultdict(lambda: 0)


        score_dict = collections.defaultdict(lambda: 0)

        for word in query:
            queryIndex[word] += 1
        
        square_val_list = []
        for word in queryIndex:
            postingList = self.get_postings_list(word)
            query_term_weight = self.get_query_term_weight(word, queryIndex, len(postingList))
            query_weight_dict[word] = query_term_weight
            square_val_list.append(query_term_weight ** 2)
        
        square_val_list.sort()
        square_sum = sum(square_val_list)

        # Get the query normalization factor 
        query_normalization_factor = math.sqrt(square_sum)

        for term in queryIndex:
            # get normalised query vector item
            postingList = self.get_postings_list(term)
            query_term_weight = query_weight_dict[term]
            query_term_weight /= query_normalization_factor

        # get normalised document vector item, then add score
        # [documentId, frequency]
        for frequencyPair in postingList:
            currScore = document_term_weights_dict[frequencyPair[0]][term] * query_term_weight
            score_dict[frequencyPair[0]] += currScore

        self.get_top_k_components(score_dict)
        return
    
    # ====================================================================
    # ====================== RANKING PROCESSING ==========================
    # ====================================================================

    def get_query_term_weight(self, query_term, termIndex, postings_list_len):
        if postings_list_len == 0:
            return 0
        return (1 + math.log(termIndex[query_term], 10)) * math.log(self.N/postings_list_len)

    def get_document_term_weight(self, document_term_frequency):
        return 1 + math.log(document_term_frequency, 10)
        
    def get_top_K_components(self, scores_dic):
        result = []
        score_tuples = [(-score, doc_id) for doc_id, score in scores_dic.items()]
        
        heapq.heapify(score_tuples)
        for i in range(self.K):
            tuple_result = heapq.heappop(score_tuples)
            result.append(tuple_result[1])

        return result

    '''
    Processes the phrasal query and returns a list of documents that are
    relevant.  
    '''
    def process_phrase(self, phrase):
        return

    def get_postings_list(term):
        return
