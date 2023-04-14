class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)
        if len(self.items) == 2:
            self.combine()

    def pop(self):
        return self.items.pop()
    
    def combine(self):
        a, b = self.items[-2:]
        result = self.AND_operation(a, b)
        self.items = self.items[:-2] + [result]

    def AND_operation(self, postings_1, postings_2):
        common_documents = []
        i = j = 0
        len_1 = len(postings_1)
        len_2 = len(postings_2)

        while (i < len_1 and j < len_2):
            
            doc_id_1 = int(postings_1[i])
            doc_id_2 = int(postings_2[j])

            # Matched postings
            if doc_id_1 == doc_id_2:
                common_documents.append(str(doc_id_1))
                i += 1
                j += 1

            elif doc_id_1 < doc_id_2: 
                # Increment postings_1 pointer
                i += 1

            else: 
                # Increment postings_2 pointer
                j += 1
        
        return common_documents


