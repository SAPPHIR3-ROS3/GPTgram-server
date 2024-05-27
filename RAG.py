from chromadb import Client
from chromadb import PersistentClient
from chromadb import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from datetime import datetime
from langchain.chat_models.ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.vectorstores.chroma import Chroma
from os import getcwd as currentDirectory
from warnings import filterwarnings

from utils import * 
from VectorChromaDB import EMBEDDING_MODEL
from VectorChromaDB import addTextDocument
from VectorChromaDB import addPDFDocument
from VectorChromaDB import queryTextCollection 

currentLogLevel = RESULT_LOG_LEVEL

EXIT_COMMAND = 'exit'
PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
END = '\033[0m'
MODEL = 'test'

MODEL = 'dolphin-llama3:8b-v2.9-q8_0'

MULTIQUERYPROMPT = PromptTemplate.from_template(
    """
    You are an AI language model assistant. Your task is to generate three
    different versions of the given user question to retrieve relevant documents from
    a vector database. By generating multiple perspectives on the user question, your
    goal is to help the user overcome some of the limitations of the distance-based
    similarity search. Provide these alternative questions separated by newlines.
    Original question: {question}
    """
)

ANSWERPROMPT =  PromptTemplate.from_template(
"""
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""
)

RELEVANCEPROMPT = PromptTemplate.from_template(
    """
    You are an AI language model assistant.Your task is to determine whether the
    given context is relevant to the user question.

    retrieved context: {context}
    user question: {question}
    ---
    (Provide a binary answer "yes" or "no, no other information is permitted, respond in lowercase) 
    Does the context contain relevant information to the user question?
    """
)

pinkText = lambda text: f'{PINK}{text}{END}'
cyanText = lambda text: f'{CYAN}{text}{END}'
yellowText = lambda text: f'{YELLOW}{text}{END}'
greenText = lambda text: f'{GREEN}{text}{END}'

def expandQuery(llm : ChatOllama, prompt, numQueries=5):
    temperature = llm.temperature
    llm.temperature = 0.9
    message = MULTIQUERYPROMPT.format(question=prompt)
    queries = set()

    for _ in range(numQueries):
        response = llm.invoke(message).content
        responseList = [query[2:] for query in response.split('\n')]
        queries.update(responseList)

    llm.temperature = temperature

    return list(queries)

def isRelevant(llm: ChatOllama, context : str, prompt : str):
    temperature = llm.temperature
    llm.temperature = 0
    
    message = RELEVANCEPROMPT.format(context=context['documents'], question=prompt)
    response = (llm.invoke(message).content).lower()

    llm.temperature = temperature

    if 'yes' in response.lower():
        return True
    
    elif 'no' in response.lower():
        return False
    
    else: raise ValueError(f'Invalid response: {response}')

if __name__ == '__main__':
    filterwarnings("ignore")
    ChromaClient = PersistentClient(currentDirectory(), Settings(anonymized_telemetry=False))
    #print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Client created")}')
    log(currentLogLevel, INFO_LOG_LEVEL, 'Client created')
    sentenceTransformer = SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL, trust_remote_code=True)
    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Embedding function created")}')
    log(currentLogLevel, INFO_LOG_LEVEL, 'Embedding function created')
    collection = ChromaClient.get_or_create_collection(name='test-collection', embedding_function=sentenceTransformer)
    #print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Collection created")}')
    log(currentLogLevel, INFO_LOG_LEVEL, 'Collection created')
    addPDFDocument(collection, 'on_the_meaning_of_life_chpt1_coda.pdf')
    #print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText(f"{collection.count()} Documents in the collection")}')
    log(currentLogLevel, INFO_LOG_LEVEL, f'{collection.count()} Documents in the collection')

    PROMPT = 'What is the meaning of life?'
    llm = ChatOllama(model=MODEL, num_gpu=32)
    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Model loaded")}')
    # log(currentLogLevel, INFO_LOG_LEVEL, 'Model loaded')
    queries = expandQuery(llm, PROMPT)
    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Query expanded")}')
    # log(currentLogLevel, INFO_LOG_LEVEL, 'Query expanded')
    results = queryTextCollection(collection, PROMPT, 20)

    # for query in queries:
        # results.extend(queryTextCollection(collection, query))

    # results.extend(queryTextCollection(collection, PROMPT, 5))

    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Retrieved documents")}')
    log(currentLogLevel, INFO_LOG_LEVEL, 'Retrieved documents')

    # uniqueResults = []

    # for result in results:
    #     if result['ids'] not in [doc['ids'] for doc in uniqueResults]:
    #         uniqueResults.append(result)
    
    uniqueResults = sorted(results, key=lambda x: x['distances'])
    # log(currentLogLevel, INFO_LOG_LEVEL, f'Documents filtered by uniqueness ({(len(uniqueResults)/ len(results)) * 100 :.2f} %  of the original results)')

    refinedResults = []

    for result in uniqueResults:
        if isRelevant(llm, result, PROMPT):
            refinedResults.append(result)
            
    log(currentLogLevel, INFO_LOG_LEVEL, f'Documents filtered by relevance ({(len(refinedResults)/ len(uniqueResults)) * 100 :.2f} % of the unique results)')


    document_context = [result['documents'] for result in uniqueResults]
    context = '\n\n---\n\n'.join(document_context)
    message = ANSWERPROMPT.format(context=context, question=PROMPT)
    response = llm.invoke(message).content
    # print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {greenText("Response generated")}')
    log(currentLogLevel, INFO_LOG_LEVEL, 'Response generated')

    # print (cyanText(message))
    # print (greenText(response))
    log(currentLogLevel, INFO_LOG_LEVEL, '', {'message': message})
    log(currentLogLevel, RESULT_LOG_LEVEL, response)
