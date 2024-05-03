from chromadb import Client
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from hashlib import sha256 as SHA256

from warnings import filterwarnings

EMBEDDING_MODEL = 'all-mpnet-base-v2'
EXIT_COMMAND = 'exit'

ChromaClient = Client(Settings(anonymized_telemetry=False))

def getID(document, metadata, data = None, uri = None):
    document = str(document)
    metadata = str(metadata)
    data = str(data)
    uri = str(uri)
    hash = SHA256((document + data + metadata + uri).encode()).hexdigest()

    return hash 

def addTextDocument(collection : Client, documents : str, metadata : dict):
    id = getID(documents, metadata)
    collection.add(documents=[documents], metadatas=[metadata], ids=[id])

def queryTextCollection(collection : Client, query : str, count : int = 3 , add_docs : bool = True, add_dists : bool = True, add_metadatas : bool = True, add_uris : bool = False, add_data : bool = False, add_embeddings : bool = False):
    includes = []

    # embeddings, documents, metadatas, uris, data, distances
    if add_docs: includes.append('documents')
    if add_dists: includes.append('distances')
    if add_metadatas: includes.append('metadatas')
    if add_uris: includes.append('uris')
    if add_data: includes.append('data')

    result = collection.query(query_texts=[query], n_results=count, include=includes)
    result = {key: result[key][0] for key in result.keys() if result[key] != None}
    orderedResult = [{key: result[key][i] for key in result.keys()} for i in range(count)]
    return orderedResult

if __name__ == '__main__':
    filterwarnings("ignore")
    sentenceTransformer = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    collection = ChromaClient.create_collection(name='test-collection', embedding_function=sentenceTransformer)
    
    addTextDocument(collection, 'This is a test document', {'author': 'Marguerite Vasquez'})
    addTextDocument(collection, 'This is another document', {'author': 'Claudia Parker'})
    addTextDocument(collection, "Dolores wouldn't have eaten the meal if she had known", {'author': 'Alan Terry'})
    addTextDocument(collection, 'There were white out conditions in the town', {'author': 'Hulda Lowe'})
    addTextDocument(collection, 'She had the gift of being able to paint songs', {'author': 'Chad Frazier'})

    while True:
        query = input('Enter a query: ')

        if query == EXIT_COMMAND:
            break

        #results = collection.query(query_texts=[query], n_results=3, include=['documents', 'distances', 'metadatas'])
        results = queryTextCollection(collection, query)
        
        #print(results)
        # for i in range(len(result['documents'][0])):
        #     print(f'{i+1} - {result["documents"][0][i]}')
        #     print(f'    Distance: {result["distances"][0][i]}')
        #     print(f'    Metadata: {result["metadatas"][0][i]}')

        for i in range(len(results)):
            print(f'{i+1} - {results[i]["documents"]}')
            print(f'    Distance: {results[i]["distances"]}')
            print(f'    Metadata: {results[i]["metadatas"]}')
            print()
