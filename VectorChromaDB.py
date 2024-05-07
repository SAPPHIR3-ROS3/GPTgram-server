from chromadb import Client
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from datetime import datetime
from easyocr import Reader
from hashlib import sha256 as SHA256
from io import BytesIO
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PIL import Image
from pdf2image import convert_from_path as convertFromPDF
from pypdf import PdfReader
from warnings import filterwarnings

EMBEDDING_MODEL = 'Alibaba-NLP/gte-large-en-v1.5'
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
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

def addPDFPartMetadata(partIndex : int, pagePartIndex : int, commonMetadata : dict):
    metadata = commonMetadata.copy()
    metadata['part index'] = partIndex
    metadata['page part'] = pagePartIndex

    return metadata

def addTextDocument(collection : Client, documents : str, metadata : dict):
    id = getID(documents, metadata)
    collection.add(documents=[documents], metadatas=[metadata], ids=[id])

def addImageDocument(collection : Client, metadata : dict, path : str, image : Image = None, save = False):
    pass

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

def extractImagesFromPDF(path : str):
    document = PdfReader(path)
    images = []

    for page in document.pages:
        for image in page.images:
            image_bytes = image.data
            image_io = BytesIO(image_bytes)
            image = Image.open(image_io)
            images.append(image)

    return images

def addPDFDocumentOCR(collection : Client, path : str, metadata : dict = None):
    if not metadata:
        commonMetadata = getPDFMetadata(path)

    pages = convertFromPDF(path)
    OCRReader = Reader(['en', 'it', 'ja', 'es', 'fr', 'de', 'ch_sim', 'ch_tra']) #TODO: needs testing
    document = []

    for i, page in enumerate(pages):
        result = OCRReader.readtext(page)
        text = ' '.join([line[1] for line in result])
        pageMetadata = dict()
        pageMetadata['raw OCR'] = result
        pageMetadata['mode'] = 'OCR'

        document.append((text, pageMetadata))

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len, is_separator_regex=False)
    partIndex = 0

    for page in document:
        currentPageIndex = 0
        parts = splitter.split_documents(page[0])

        for i in range(len(parts)):
            for key in commonMetadata.keys():
                parts[i].metadata[key] = str(commonMetadata[key])

            metadata = addPDFPartMetadata(partIndex, currentPageIndex, commonMetadata)
            metadata['mode'] = 'OCR'
            id = getID(parts[i], metadata, uri=path)
            currentPageIndex += 1
            partIndex += 1
            collection.add(documents=[parts[i].page_content], metadatas=[metadata], uris=[path], ids=[id])


def addPDFDocument2(collection : Client, path : str, metadata : dict = None):
    if not metadata:
        commonMetadata = getPDFMetadata(path)

    document = PyPDFLoader(path, extract_images=True).load()
    images = extractImagesFromPDF(path) #TODO: Add images to the collection

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len, is_separator_regex=False)
    parts = splitter.split_documents(document)

    lastPage = None
    currentPartIndex = 0

    for i in range(len(parts)):
        page = parts[i].metadata.get("page")

        if lastPage == page: currentPartIndex += 1
        else: currentPartIndex = 0

        for key in commonMetadata.keys():
            parts[i].metadata[key] = str(commonMetadata[key])

        metadata = addPDFPartMetadata(i, currentPartIndex, commonMetadata)
        metadata['mode'] = 'pyPDF'
        id = getID(parts[i], metadata, uri=path)
        lastPage = page
        collection.add(documents=[parts[i].page_content], metadatas=[metadata], uris=[path], ids=[id])

    #addPDFDocumentOCR(collection, path, metadata)

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
    sentenceTransformer = SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL, trust_remote_code=True)
    collection = ChromaClient.create_collection(name='test-collection', embedding_function=sentenceTransformer)
    
    # addTextDocument(collection, 'This is a test document', {'author': 'Marguerite Vasquez'})
    # addTextDocument(collection, 'This is another document', {'author': 'Claudia Parker'})
    # addTextDocument(collection, "Dolores wouldn't have eaten the meal if she had known", {'author': 'Alan Terry'})
    # addTextDocument(collection, 'There were white out conditions in the town', {'author': 'Hulda Lowe'})
    # addTextDocument(collection, 'She had the gift of being able to paint songs', {'author': 'Chad Frazier'})
    
    addPDFDocumentOCR(collection, PDFPATH)
    quit()

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
