class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)
        if len(self.items) == 2:
            self.combine()

    def pop(self):
        return self.items.pop()
    
    def isEmpty(self):
        return len(self.items) == 0
    
    def combine(self):
        a, b = self.items[-2:]
        result = self.AND_operation(a, b)
        self.items = self.items[:-2] + [result]

    def AND_operation(self, postings_1, postings_2):
        print("applying AND operation...")
        print(postings_1, postings_2)
        common_documents = postings_1 & postings_2
        return common_documents


