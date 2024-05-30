from chromadb import Client
from chromadb import Collection
from chromadb import PersistentClient
from chromadb.config import Settings
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from datetime import datetime
from easyocr import Reader
from hashlib import sha256 as SHA256
from io import BytesIO
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.document_loaders import UnstructuredImageLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_core.documents.base import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from numpy import array as Array
from os import getcwd as currentDirectory
from PIL import Image
from pdf2image import convert_from_path as convertFromPDF
from pypdf import PdfReader
from warnings import filterwarnings
from transformers import BlipForConditionalGeneration 
from transformers import BlipProcessor
from transformers import ViTForImageClassification as Model
from transformers import ViTImageProcessor as Processor

from Scripts.utils import *

currentLogLevel = INFO_LOG_LEVEL

EMBEDDING_MODEL = 'Alibaba-NLP/gte-large-en-v1.5'
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
EXIT_COMMAND = 'exit'
POPPLERPATH = '../dependencies/windows/poppler-24.02.0/Library/bin'
PDFPATH = 'on_the_meaning_of_life_chpt1_coda.pdf'

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

ChromaClient = None
SentenceTransformer = None

def getID(document, metadata : dict, data = None, uri = None):
    document = str(document)
    metadata = str(metadata)
    data = str(data)
    uri = str(uri)
    hash = SHA256((document + data + metadata + uri).encode()).hexdigest()

    return hash 

def doesExists(collection : Collection, id : str):
    document = collection.get(id)

    return len(document['ids']) != 0

def getPDFMetadata(documentPath : str):
    documentMetadata = PdfReader(documentPath).metadata
    metadata = {
        'title': str(documentMetadata.get('title', 'Unknown title')),
        'author': str(documentMetadata.get('author', 'Unknown author')),
        'creation date': str(documentMetadata.get('creationDate', 'Unknown date')),
        'language': str(documentMetadata.get('language', 'Unknown language')),
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

def addTextDocument(collection : Collection, documents : str, metadata : dict):
    id = getID(documents, metadata)

    if not doesExists(collection, id):
        collection.add(documents=[documents], metadatas=[metadata], ids=[id])

def getClassImage(imagepath):
    model = Model.from_pretrained('google/vit-large-patch16-224')
    processor = Processor.from_pretrained('google/vit-large-patch16-224')
    image = Image.open(imagepath).convert('RGB')
    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_idx = logits.argmax(-1).item()
    classification = str(model.config.id2label[predicted_class_idx])
    
    return classification

def getCaptionImage(imagepath):
    image = Image.open(imagepath).convert('RGB')
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
    inputs = processor(images=image, return_tensors="pt")
    outputs = model.generate(**inputs)
    caption = processor.decode(outputs[0], skip_special_tokens=True)

    return caption

def getImageMetadata(imagepath):
    metadata = dict()
    metadata['adding date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata['uri'] = imagepath
    metadata['type'] = imagepath.split('.')[-1]
    metadata['classification'] = getClassImage(imagepath)
    metadata['caption'] = getCaptionImage(imagepath)

    return metadata

def addImageDocument(collection : Collection, path : str, metadata : dict = None, name : str = None):
    if not metadata:
        metadata = getImageMetadata(path)
    
    document = Document(path if not name else name)
    image = Image.open(path).convert('RGB')
    id = getID(image, metadata, uri=path)
    
    if not doesExists(collection, id):
        collection.add(documents=[document], metadatas=[metadata], ids=[id], uris=[path])

def addPDFDocumentUnstructured(collection : Collection, path : str, metadata : dict = None):
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

        if not doesExists(collection, id):
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

def addPDFDocumentOCR(collection : Collection, path : str, metadata : dict = None):
    if not metadata:
        commonMetadata = getPDFMetadata(path)

    pages = [Array(page) for page in convertFromPDF(path, poppler_path=POPPLERPATH)]
    OCRReader = Reader(['en', 'it', 'es', 'fr', 'de'], gpu=True) #TODO: needs testing
    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("OCR: Reader loaded")}: {path}')
    log(currentLogLevel, INFO_LOG_LEVEL, 'OCR: Reader loaded')
    
    document = []

    for i, page in enumerate(pages):
        result = OCRReader.readtext(page)
        text = ' '.join([line[1] for line in result])
        pageMetadata = dict()
        pageMetadata['raw OCR'] = result
        pageMetadata['mean confidence'] = str(sum([line[2] for line in result]) / len(result))
        pageMetadata['mode'] = 'OCR'
        pageMetadata['page'] = i
        pageDocument = Document(page_content=text, metadata=pageMetadata)

        document.append(pageDocument)

    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("OCR: Document loaded")}: {path}')
    log(currentLogLevel, INFO_LOG_LEVEL, 'OCR: Document loaded')

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len, is_separator_regex=False)
    parts = splitter.split_documents(document)
    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("OCR: Document splitted")}: {len(parts)}')
    log(currentLogLevel, INFO_LOG_LEVEL, f'OCR: Document splitted: {len(parts)}')

    lastPage = None
    currentPartIndex = 0
    
    for i in range(len(parts)):
        page = parts[i].metadata.get("page")

        if lastPage == page: currentPartIndex += 1
        else: currentPartIndex = 0

        for key in commonMetadata.keys():
            parts[i].metadata[key] = str(commonMetadata[key])

        metadata = addPDFPartMetadata(i, currentPartIndex, commonMetadata)
        metadata['mode'] = 'OCR'
        metadata['page'] = page
        id = getID(parts[i], metadata, uri=path)

        lastPage = page

        if not doesExists(collection, id):
            metadata['adding date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            collection.add(documents=[parts[i].page_content], metadatas=[metadata], uris=[path], ids=[id])

    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("OCR: Document added")}: {path}')
    log(currentLogLevel, INFO_LOG_LEVEL, f'OCR: Document added: {path}')

def addPDFDocument(collection : Collection, path : str, metadata : dict = None, images : bool = False, imagesPath : str = None):
    if not metadata:
        commonMetadata = getPDFMetadata(path)

    documentName = datetime.now().strftime('%Y%m%d') + path.split('/')[-1].split('.')[0]
    document = PyPDFLoader(path, extract_images=True).load()
    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("PyPDF: Document loaded")}: {path}')
    log(currentLogLevel, INFO_LOG_LEVEL, f'PyPDF: Document loaded: {path}')
    images = extractImagesFromPDF(path) #TODO: Add images to the collection
    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("PyPDF: Images extracted")}: {len(images)}')
    log(currentLogLevel, INFO_LOG_LEVEL, f'PyPDF: Images extracted: {len(images)}')

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len, is_separator_regex=False)
    parts = splitter.split_documents(document)
    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("PyPDF: Document splitted")}: {len(parts)}')
    log(currentLogLevel, INFO_LOG_LEVEL, f'PyPDF: Document splitted: {len(parts)}')

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
        metadata['page'] = page
        id = getID(parts[i], metadata, uri=path)
        lastPage = page

        if not doesExists(collection, id):
            metadata['adding date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            collection.add(documents=[parts[i].page_content], metadatas=[metadata], uris=[path], ids=[id])

    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("PyPDF: Document added")}: {path}')
    log(currentLogLevel, INFO_LOG_LEVEL, f'PyPDF: Document added: {path}')

    if images: # TODO: needs testing
        for i, image in enumerate(images):
            path = f'{imagesPath}/{documentName+str(i+1)}.png'
            image.save(path)
            addImageDocument(collection, path)

def addPDFDocumentMultiModal(collection : Collection, path : str, metadata : dict = None, images : bool = False, imagesPath : str = None):
    addPDFDocument(collection, path, metadata, images, imagesPath)
    addPDFDocumentOCR(collection, path, metadata)

def queryTextCollection(collection : Collection, query : str, count : int = 3 , add_docs : bool = True, add_dists : bool = True, add_metadatas : bool = True, add_uris : bool = False, add_data : bool = False, add_embeddings : bool = False):
    includes = []

    # embeddings, documents, metadatas, uris, data, distances
    if add_docs: includes.append('documents')
    if add_dists: includes.append('distances')
    if add_metadatas: includes.append('metadatas')
    if add_uris: includes.append('uris')
    if add_data: includes.append('data')

    result = collection.query(query_texts=[query], n_results=count, include=includes)
    result = {key: result[key][0] for key in result.keys() if result[key] != None}
    orderedResult = [{key: result[key][i] for key in result.keys()} for i in range(len(result['documents']))]
    
    return orderedResult

def queryImageCollection(collection : Collection, imagepath : str, count : int = 3, add_docs : bool = True, add_dists : bool = True, add_metadatas : bool = True, add_uris : bool = False, add_data : bool = False, add_embeddings : bool = False):
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

def createOrGetUserVectorDatabase(user: str):
    SentenceTransformer = SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL, trust_remote_code=True)
    UserClient = PersistentClient(f'../users-data/{user}', Settings(anonymized_telemetry=False))
    
    if not UserClient:
        return None
    
    userCollection  = UserClient.get_or_create_collection(name='user-collection', embedding_function=SentenceTransformer)

    if not userCollection:
        return None
    
    mediaCollection = UserClient.get_or_create_collection(name='media-collection', embedding_function=OpenCLIPEmbeddingFunction(), data_loader=ImageLoader())

    if not mediaCollection:
        return None
    
    return UserClient

def getUserTextCollection(user: str, chatId : str):
    UserClient = createOrGetUserVectorDatabase(user)
    SentenceTransformer = SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL, trust_remote_code=True)
    UserCollection = UserClient.get_or_create_collection(name='user-collection', embedding_function=SentenceTransformer) #TODO: need to implement a workaround of the 3-63 characters limit of chroma db

    return UserCollection

def addTextDocumentToUserCollection(user: str, document: str, metadata: dict, AI: str = '', AIDocument: str = '', AIMetadata: dict = None):
    if not metadata:
        metadata = dict()
        metadata['adding date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata['mode'] = 'text'
        metadata['author'] = user
        log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} metadata created')

    UserClient = createOrGetUserVectorDatabase(user)
    log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} database loaded')
    UserColletion = UserClient.get_or_create_collection(name='user-collection', embedding_function=SentenceTransformer)
    log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} collection loaded')
    addTextDocument(UserColletion, document, metadata)
    log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} document added')

    if AI and AIDocument:
        if not AIMetadata:
            AIMetadata = dict()
            AIMetadata['adding date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            AIMetadata['author'] = AI
            AIMetadata['mode'] = 'AI'
            log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} AI metadata created')

        addTextDocument(UserColletion, AIDocument, AIMetadata)
        log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} AI document added')

def queryUserTextCollection(user: str, query: str, count: int = 3, add_docs: bool = True, add_dists: bool = True, add_metadatas: bool = True, add_uris: bool = False, add_data: bool = False, add_embeddings: bool = False):
    UserClient = createOrGetUserVectorDatabase(user)
    log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} database loaded')
    UserCollection = UserClient.get_or_create_collection(name='user-collection', embedding_function=SentenceTransformer)
    log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} collection loaded')
    result = queryTextCollection(UserCollection, query, count, add_docs, add_dists, add_metadatas, add_uris, add_data, add_embeddings)
    log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} query executed')
    
    return result

if __name__ == '__main__':
    filterwarnings("ignore")
    ChromaClient = PersistentClient(currentDirectory(), Settings(anonymized_telemetry=False))

    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Starting...")}')
    sentenceTransformer = SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL, trust_remote_code=True)
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Model loaded")}: {EMBEDDING_MODEL}')
    collection = ChromaClient.create_collection(name='test-collection', embedding_function=SentenceTransformer)
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Collection created")}: test-collection')
    imageLoader = ImageLoader()
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Image loader loaded")}')
    openCLIP = OpenCLIPEmbeddingFunction()
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("OpenCLIP loaded")}')
    # mediaCollection = ChromaClient.create_collection(name='media-collection', embedding_function=openCLIP, data_loader=imageLoader)
    # addTextDocument(collection, 'This is a test document', {'author': 'Marguerite Vasquez'})
    # addTextDocument(collection, 'This is another document', {'author': 'Claudia Parker'})
    # addTextDocument(collection, "Dolores wouldn't have eaten the meal if she had known", {'author': 'Alan Terry'})
    # addTextDocument(collection, 'There were white out conditions in the town', {'author': 'Hulda Lowe'})
    # addTextDocument(collection, 'She had the gift of being able to paint songs', {'author': 'Chad Frazier'})
    
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText(f"{collection.count()} Documents added")}')
    #addPDFDocumentMultiModal(collection, PDFPATH)
    # addImageDocument(mediaCollection, 'testimages/animals/illustration/white/1.png')
    # addImageDocument(mediaCollection, 'testimages/background/vector/white/2.png')
    # addImageDocument(mediaCollection, 'testimages/buildings/photo/white/1.jpg')
    # addImageDocument(mediaCollection, 'testimages/business/illustration/white/3.jpg')
    # addImageDocument(mediaCollection, 'testimages/computer/vector/white/2.png')
    # addImageDocument(mediaCollection, 'testimages/education/photo/white/2.jpg')
    # addImageDocument(mediaCollection, 'testimages/fashion/illustration/white/1.jpg')
    # addImageDocument(mediaCollection, 'testimages/feelings/vector/white/1.png')
    # addImageDocument(mediaCollection, 'testimages/food/photo/white/1.jpg')
    # addImageDocument(mediaCollection, 'testimages/health/illustration/white/4.jpg')
    # addImageDocument(mediaCollection, 'testimages/industry/vector/white/2.png')
    
    print()

    while True:
        query = input('Enter a query: ')

        if query == EXIT_COMMAND:
            break
        
        results = queryTextCollection(collection, query)
        # results = queryImageCollection(mediaCollection, query, 5)

        # for i in range(len(results)):
        #     print(f'{greenText(i+1)} - {results[i]["documents"]}')
        #     print(f'    Distance: {results[i]["distances"]}')
        #     print(f'    Metadata: {results[i]["metadatas"]}')
        #     print()

        for result in results:
            print(result)
            print()
        
        print()

    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Exiting...")}')
