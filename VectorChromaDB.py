from chromadb import Client
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from datetime import datetime
from hashlib import sha256 as SHA256
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from warnings import filterwarnings

EMBEDDING_MODEL = 'all-mpnet-base-v2'
CHUNK_SIZE = 350
CHUNK_OVERLAP = 75
EXIT_COMMAND = 'exit'
PDFPATH = 'Relationships between physhical properties and sequence in silkworm silks.pdf'

PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
END = '\033[0m'
MODEL = 'test'


pinkText = lambda text: f'{PINK}{text}{END}'
cyanText = lambda text: f'{CYAN}{text}{END}'
yellowText = lambda text: f'{YELLOW}{text}{END}'
greenText = lambda text: f'{GREEN}{text}{END}'

ChromaClient = Client(Settings(anonymized_telemetry=False))

def getID(document, metadata : dict, data = None, uri = None):
    document = str(document)
    metadata = str(metadata)
    data = str(data)
    uri = str(uri)
    hash = SHA256((document + data + metadata + uri).encode()).hexdigest()

    return hash 

def getPDFMetadata(documentPath : str):
    documentMetadata = PdfReader(documentPath).metadata
    metadata = {
        'title': str(documentMetadata.get('title', 'Unknown title')),
        'author': str(documentMetadata.get('author', 'Unknown author')),
        'creation date': str(documentMetadata.get('creationDate', 'Unknown date')),
        'language': str(documentMetadata.get('language', 'Unknown language')),
        'adding date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'uri': documentPath
    }

    return metadata

def getPDFPartMetadata(part : int, previusPart = None, nextPart = None, commonMetadata = None):
    metadata = commonMetadata.copy()
    metadata['part'] = part
    metadata['previusPart'] = previusPart
    metadata['nextPart'] = nextPart

    return metadata

def addTextDocument(collection : Client, documents : str, metadata : dict):
    id = getID(documents, metadata)
    collection.add(documents=[documents], metadatas=[metadata], ids=[id])

def addPDFDocument(collection : Client, path : str, metadata : dict = None):
    if not metadata:
        metadata = getPDFMetadata(path)

    document = UnstructuredPDFLoader(path).load()
    id = getID(document, metadata, uri=path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    parts = splitter.split_documents(document)
    
    for i in range(len(parts)):
        if i == 0:
            partMetadata = getPDFPartMetadata(i, nextPart = i + 1, commonMetadata = metadata)
        elif i == len(parts) - 1:
            partMetadata = getPDFPartMetadata(i, previusPart = i - 1, commonMetadata = metadata)
        else:
            partMetadata = getPDFPartMetadata(i, previusPart = i - 1, nextPart = i + 1, commonMetadata = metadata)

        for key in partMetadata.keys():
            partMetadata[key] = str(partMetadata[key])

        id = getID(parts[i], partMetadata, uri=path)
        # print(f'{greenText("part")}: {parts[i].page_content}')
        # print(f'{greenText("metadata")}: {parts[i].metadata}')
        # print(f'{greenText("metadata")}: {[partMetadata]}')
        # print(f'{greenText("id")}: {id}')
        # print(f'{greenText("uri")}: {path}')
        # print()
        collection.add(documents=[parts[i].page_content], metadatas=[partMetadata], ids=[id], uris=[path])


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
    
    # addTextDocument(collection, 'This is a test document', {'author': 'Marguerite Vasquez'})
    # addTextDocument(collection, 'This is another document', {'author': 'Claudia Parker'})
    # addTextDocument(collection, "Dolores wouldn't have eaten the meal if she had known", {'author': 'Alan Terry'})
    # addTextDocument(collection, 'There were white out conditions in the town', {'author': 'Hulda Lowe'})
    # addTextDocument(collection, 'She had the gift of being able to paint songs', {'author': 'Chad Frazier'})
    
    addPDFDocument(collection, PDFPATH)

    while True:
        query = input('Enter a query: ')

        if query == EXIT_COMMAND:
            break
        
        results = queryTextCollection(collection, query, 5)

        for i in range(len(results)):
            print(f'{greenText(i+1)} - {results[i]["documents"]}')
            print(f'    Distance: {results[i]["distances"]}')
            print(f'    Metadata: {results[i]["metadatas"]}')
            print()
