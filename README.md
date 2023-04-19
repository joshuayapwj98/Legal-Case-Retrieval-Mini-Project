# CS3245-Legal-Case-Retrieval-Mini-Project

This is the README file for A0222182R's, A0222371R's, A0218297U's and A0217487U's submission
Email(s): e0559714@u.nus.edu, e0559903@u.nus.edu,

== Python Version ==

We're using Python Version <3.10.9> for this assignment.

== General Notes about this assignment ==

###Description
This program implements indexing and searching techniques for Legal Case Retrieval from a set of training data given to it. It is capable of finding the relevant docIDs in response to the query.

These documents are ordered by relevance, with the first document being most relevant. For documents with the same relevance, they are further sorted by the increasing order of the docIDs.

###How to use
To build the indexing script, index.py, run:
$ python3 index.py -i dataset-file -d dictionary-file -p postings-file
which will store your dictionary into dictionary-file and postings into postings-file.
Three other files, all_doc_ids.txt, document.txt and pointers.txt will also be generated.

To run the searching script, search.py, run:
$ python3 search.py -d dictionary-file -p postings-file -q query-file -o output-file-of-results
which will store the queries results into output-file-of-results.

###About Indexing
We created a VectorSpaceModel class that helps with the indexing of all documents from dataset-file.

####Dictionary as Output File
The dictionary file contains information of all terms in the dataset. In order to reduce storage, we applied two dictionary compression techniques, namely dictionary as a string and blocking with block size of 4. We stored all terms as a single string, separated by the term's length.

The dictionary file is written in the form of as such.
|term_len|term|term_len2|term2...

####Postings as Output File
In order to support phrasel queries, we included positional indexes in our postings file. However, this is done at the cost of storage space, as it would significantly increase the size of our postings file. To mitigate the impact, gap encoding technique is applied to both docID and position.

The postings file contains information written in the form of as such.
term documentFrequency
docID,wt,d:position1 position2… gapEncodedID,wt,d:position1 position2…
term2 documentFrequency
docID,wt,d:position1 position2… gapEncodedID,wt,d:position1 position2…
…
where wt,d is the weighted term frequency = (1 + log(tf)), and tf is the term frequency of the term t in docID.

####Other Output Files
Additionally, three new files, namely all_doc_ids.txt and document.txt will also be generated after the indexing.

The all_doc_ids.txt is an output file containing the ID of all documents, sorted in increasing order, separated by a single space.

While document.txt is an output file written in the form of as such.
total_num_of_doc docID,len_of_doc docID2,len_of_doc ...
where len_of_doc is the length of the document with docID in the vector space

Lastly, the pointers.txt is an output file containing the pointers to dictionary and postings files. It is written in the form of as such.
DictPtr,PostingPtr1,PostingPtr2,PostingPtr3,PostingPtr4
DictPtr,PostingPtr1,PostingPtr2,PostingPtr3,PostingPtr4
...
where DictPtr points to the start of the next 4 terms in dictionary file, and the 4 PostingPtr each points to the start of the postings of the next term.

###About parse_data
This method is responsibile for reading and extracting the data from dataset. As some of the legal cases share the same document id, we concatenate the information of these cases together as one. The method then sorts all documents by increasing id. This sorted list of ids is then written into the all_doc_ids.txt output file as mentioned previously. Finally, the method returns useful data such as all_doc_ids and content to be used in the construct method.

###About construct
This method is responsible for constructing the indexing of all terms and their postings. It loops through every document, tokenizes every terms and store information in various data strucutures for writing of output files.

####Tokenisation
First, we obtain a sorted list of all document IDs. Then, we construct the index by looping through each document ID and tokenising every term in each document. The tokenisation of term is done using the NLTK tokenizers, nltk.sent_tokenize() and nltk.word_tokenize(). We then use NLTK Porter stemmer (class nltk.stem.porter) to do stemming. Lastly, we did case-folding to reduce all words to lower case.

Unlike HW2, we did not make use of techniques such as removing punctuation and digits. We also did not remove numbers. This is so that users can still be able to query using numbers. Also, by keeping the punctuations and storing the exact positions of terms, we ensure better accuracy for phrasel queries.

####Document Frequency and Positional Index
In construct, we also count the number of document frequency of each term, as well as the positions of each term appearing in a document. These are later stored in term_doc_freq = { term : doc_freq } and term_id_pos = { term : { docID : [position...] } }

###About construct_weighted_postings
This method takes in a list of all document ids and a dictionary of all the positions of terms in the documents, it constructs and returns the document lengths and postings for writing of output files.

####Weighted Document Term
The construct_weighted_postings method counts the term frequnecy (tf) from the positions, and calculates the weighted term frequency (w-tf), known as the log_term_freq_weighted. This is done using the formula, w-tf = 1 + log(tf), where log is base 10 logarithm.

####Document Length
The method also calculates the document length doc_len of each document in the vector space. The length of document in the vector space can be calculated by summing the squares of all w-tf of the terms presented in the document, and taking the sqaure root of the summation result.

###About write_output_files
This method takes in a sorted dictionary of terms, a dictionary of term and document frequency, and postings, and write out the final content for dictionary, postings and pointers files.

####Gap Encoding of Document ID & Term Positions
Gap encoding of document id and positions are done by substracting the previous values of document id and term position from the current values. Given a term, we retrieve all the document ids and weighted-tf from the input postings, and concatenate the information into a string variable named final_postings.

The posting reference is updated by adding the result of the encoded length of posting content in utf-8. We then store the value of the posting reference in a list named posting_pointer.

####Dictionary as a String & Blocking
We are using blocking with block size 4 for dictionary, in another words, for every four posting pointers stored in the pointers.txt file, there would be one dictionary pointer. As such, our algorithm keeps track of the length of posting_pointer at each instance.

If the length of posting_pointer is smaller than block size, i.e. 4 in our case, we concatenate the term into a temporary accumulated string acc_dictionary_content, and the algorithm continues.

If the length of the posting_pointer equals to the block size, we add the term into the acc_dictionary_content, and updates the pointers content, i.e. DictPtr, PostingPtr1, PostingPtr2, PostingPtr3, PostingPtr4.

The dictionary reference is updated by adding the result of the encoded length of dictionary content in utf-8. We then finally reset the value of posting_pointer and acc_dictionary_content.

The algorithm repeats until all contents of dictionary, postings and pointers are generated. They are then written into the respective output files.

###About Querying
####Search

== Files included with this submission ==

1. README.txt - a summary write up about the program, how to run and how it works
2. index.py - the main program to run the indexing, which calls vector_space_model.py
3. index-vector_space_model.py - contains the methods to index the terms and writes the results into dictionary-file, postings-file, all_doc_ids.txt, document.txt and pointers.txt
4. dictionary.txt - a dictionary text file containing all terms as a string, separated by their term length
5. postings.txt - a posting text file containing information about term, document frequency, document id, weighted-tf and positional indexes
6. all_doc_ids.txt - a text file containing all the document IDs
7. document.txt - a text file containing total number of docs and all IDs sorted in increasing order
8. pointers.txt - a text file containing pointers to dictionary and posting files
9. search.py - the main program to run the searching, which calls vector_search.py
10.

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] I/We, A0222182R, A0222371R, A0218297U and A0217487U certify that I/we have
followed the CS 3245 Information Retrieval class guidelines for homework assignments.
In particular, I/we expressly vow that I/we have followed the Facebook rule in
discussing with others in doing the assignment and did not take notes (digital or
printed) from the discussions.

[ ] I/We, A0000000X, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

We suggest that we should be graded as follows:

<Please fill in>

== References ==

<Please list any websites and/or people you consulted with for this
assignment and state their role>
