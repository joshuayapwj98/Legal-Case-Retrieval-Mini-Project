from stack import Stack

class QueryParser:

    def __init__(self):
        pass

    def process_query(self, query):
        print("processing query...")

        if 'AND' in query:
            results = self.process_boolean_query(query)
        else:
            results = self.process_freetext_query(query)


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
    
    '''
    Processes the phrasal query and returns a list of documents that are
    relevant.  
    '''
    def process_phrase(self, phrase):


    def get_postings_list(term):

