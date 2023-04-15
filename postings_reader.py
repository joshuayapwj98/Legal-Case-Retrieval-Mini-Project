class PostingsReader:

    def __init__(self):
        # Load all of the pointers from pointers.txt into memory
        self.pointer_data = []
        with open('pointers.txt', 'r') as f:
            self.pointer_data = f.read().split()

    '''
    Returns the pointer to the position of the term in postings.txt
    '''
    def get_postings_ptr(self, query_term):
        postings_ptr = self.binary_search(query_term)
        return postings_ptr

    '''
    Returns the doc_freq of the term from postings.txt
    '''
    def get_doc_freq(self, postings_ptr):
        with open('postings.txt', 'r') as f: 
            line = f.readline()
            values = line.split()
            print("doc_freq for term ", values[0], "is ", values[1])
            return values[1]

    '''
    Returns the integer pointer to the postings list, or -1 if not found. 
    '''
    def binary_search(self, query_term):
        # Binary search through the DictPtrs 
        left = 0 
        right = len(self.pointer_data) - 1

        while left <= right:
            mid = (left + right) // 2
            curr_block = self.pointer_data[mid].split(',') # E.g. 12,24968,41204,66916,209555
            
            dict_ptr = int(curr_block[0])
            f = open('dictionary.txt', 'r')
            f.seek(dict_ptr, 0) # Points to |7|carrara|7|carrati|8|carratti|5|carri...

            # Linear search through each block
            # E.g. |7|claim55|7|claim62|8|claimabl|8|claimant
            num_of_terms = len(curr_block) - 1
            first_term = ""
            last_term = ""
            for i in range(num_of_terms):
                count = 0 
                length_of_term = ''

                while count < 2: 
                    next_char = f.read(1)
                    if next_char == '|':
                        count += 1
                    else: 
                        length_of_term += next_char

                term = f.read(int(length_of_term))

                if i == 0:
                    first_term = term
                if i == num_of_terms - 1:
                    last_term = term

                # Return if matching 
                if query_term == term:
                    return int(curr_block[i + 1]) 
                
            # Terms did not match
            if query_term < first_term: 
                right = mid - 1

            elif query_term > last_term:
                left = mid + 1
        
        print("Term not found in dictionary...")
        return -1 

