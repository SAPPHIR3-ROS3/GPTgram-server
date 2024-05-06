from chromadb import Client
from chromadb.config import Settings
from datetime import datetime
from hashlib import sha256 as SHA256
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from warnings import filterwarnings

EMBEDDING_MODEL = 'all-mpnet-base-v2'
EXIT_COMMAND = 'exit'
COLLECTION_NAME = 'test-collection'

def getID(document, metadata : dict, data = None, uri = None):
    document = str(document)
    metadata = str(metadata)
    data = str(data)
    uri = str(uri)
    hash = SHA256((document + data + metadata + uri).encode()).hexdigest()

    return hash

def getPDFMetadata(documentPath):
    documentMetadata = PdfReader(documentPath).metadata
    metadata = {
        'title': documentMetadata.get('title', 'Unknown title'),
        'author': documentMetadata.get('author', 'Unknown author'),
        'creation date': documentMetadata.get('creationDate', 'Unknown date'),
        'language': documentMetadata.get('language', 'Unknown language'),
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

def addPDFDocument(collection, path : str, metadata : dict):
    document = UnstructuredPDFLoader(path).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=350, chunk_overlap=75)
    parts = splitter.split(document)

    for i in range(len(parts)):
        if i == 0:
            partMetadata = getPDFPartMetadata(i, nextPart = i + 1, commonMetadata = metadata)
        elif i == len(parts) - 1:
            partMetadata = getPDFPartMetadata(i, previusPart = i - 1, commonMetadata = metadata)
        else:
            partMetadata = getPDFPartMetadata(i, previusPart = i - 1, nextPart = i + 1, commonMetadata = metadata)
        
        id = getID(parts[i], partMetadata, uri=path)

        # collection.add(documents=[parts[i]], metadatas=[partMetadata], ids=[id], uris=[path])

    #id = getID(document, metadata, uri=path)
    #collection.add(documents=[document], metadatas=[metadata], ids=[id], uris=[path])

if __name__ == '__main__':
    filterwarnings("ignore")
    embeddingModel = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    ChromaClient = Chroma(COLLECTION_NAME, client=Client(Settings(anonymized_telemetry=False)), embedding_function=embeddingModel)
    ChromaClient.add_texts(['This is a test document'], [{'author': 'Marguerite Vasquez'}])
    ChromaClient.add_texts(['This is another document'], [{'author': 'Claudia Parker'}])
    ChromaClient.add_texts(["Dolores wouldn't have eaten the meal if she had known"], [{'author': 'Alan Terry'}])
    ChromaClient.add_texts(['There were white out conditions in the town'], [{'author': 'Hulda Lowe'}])
    ChromaClient.add_texts(['She had the gift of being able to paint songs'], [{'author': 'Chad Frazier'}])
    #Chroma.from_documents(client=ChromaClient, collection_name=COLLECTION_NAME, documents=)

    while True:
        query = input('Enter a query: ')

        if query == EXIT_COMMAND:
            break
        
        results = ChromaClient.similarity_search_with_score(query, k=3)

        for i in range(len(results)):
            print(f'{i+1} - {results[i][0].page_content}')
            print(f'    Distance: {results[i][1]}')
            print(f'    Metadata: {results[i][0].metadata}')
            print()
    