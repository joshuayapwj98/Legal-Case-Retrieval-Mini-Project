import io

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
        print(query_term)
        postings_ptr = self.binary_search(query_term)

        # Prints the postings list of the term
        if postings_ptr != -1: 
            with open("postings.txt", 'r') as f:
                f.seek(postings_ptr, 0)
                # print("postings list retrieved:", f.readline())

        return postings_ptr

    '''
    Returns the doc_freq of the term from postings.txt
    '''
    def get_doc_freq(self, postings_ptr):
        with open('postings.txt', 'r') as f: 
            line = f.readline()
            values = line.split()
            # print("doc_freq for term ", values[0], "is ", values[1])
            return values[1]

    '''
    Returns the integer pointer to the postings list, or -1 if not found. 
    '''
    def binary_search(self, query_term):

        # print("running binary search...")
        # Binary search through the DictPtrs 
        left = 0 
        right = len(self.pointer_data) - 1

        f = open('dictionary-17137.txt', 'rb')
        f.seek(3951151, 0) # Points to |11|read‑onli|8|read—i
        test = f.read(15)
        print('TEST', test.decode('utf-8'))
        # print(f.read(15)) # Prints |11|read‑onli|8
        f.seek(3951166, 0) # increment by 15 Points to |8|read—i|10|re
        print(f.read(15))

        while left <= right:
            mid = (left + right) // 2
            curr_block = self.pointer_data[mid].split(',') # E.g. 12,24968,41204,66916,209555
            print(curr_block)
            dict_ptr = int(curr_block[0])
            f = open('dictionary-17137.txt', 'rb')
            f.seek(dict_ptr, 0) # Points to |7|carrara|7|carrati|8|carratti|5|carri...

            # Linear search through each block
            # E.g. |7|claim55|7|claim62|8|claimabl|8|claimant
            num_of_terms = len(curr_block) - 1
            first_term = ""
            last_term = ""
            for i in range(num_of_terms):
                count = 0 
                length_of_term = b''

                while count < 2: 
                    next_char = f.read(1)
                    if next_char == b'|':
                        count += 1
                    else: 
                        length_of_term += next_char

                # print('hello', length_of_term)
                term = f.read(int(length_of_term.decode('utf-8')))
                term = term.decode('utf-8')
                # print(term)

                if i == 0:
                    first_term = term
                if i == num_of_terms - 1:
                    last_term = term

                # Return if matching 
                if query_term == term:
                    # print('postings list pointer:', int(curr_block[i + 1]) )
                    return int(curr_block[i + 1]) 
                
            # Terms did not match
            if query_term < first_term: 
                right = mid - 1

            elif query_term > last_term:
                left = mid + 1

            # Terminating clause when term is not found...
            else: 
                break
        
        # print("Term not found in dictionary...")
        return -1 