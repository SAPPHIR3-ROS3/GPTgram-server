from chromadb import Client
from chromadb import Collection
from chromadb import PersistentClient
from chromadb import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from datetime import datetime
from json import dump
from json import load
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_community.chat_models.ollama import ChatOllama
from os import getcwd as currentDirectory
from warnings import filterwarnings

from Scripts.utils import * 
from Scripts.VectorChromaDB import EMBEDDING_MODEL
from Scripts.VectorChromaDB import addPDFDocument
from Scripts.VectorChromaDB import getUserTextCollection
from Scripts.VectorChromaDB import queryTextCollection

currentLogLevel = RESULT_LOG_LEVEL

EXIT_COMMAND = 'exit'
SEPARATOR = '\n\n---\n\n'
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

TITLECHATPROMPT = ChatPromptTemplate.from_template(
    """
    You are an AI language model assistant. Your task is to generate a title 
    for the chat between the user and the AI. The title should be a concise
    summary of the chat content and as short as possible.
    
    user: {user}
    AI: {AI}

    ---

    (Provide only the title for the chat, no other information is permitted)
    What is the title of the chat?
    """
)

class Response:
    def __init__(self, context: list, response : str = ''):
        self.response = response
        self.context = context

    def __str__(self):
        return self.response
    
    def getContext(self):
        return self.context
    
    def getFormattedContext(self):
        formattedContext = '\n\n---\n\n'.join([doc['documents'] for doc in self.context])
        return formattedContext
    
    def setResponse(self, response):
        self.response = response
    
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

def generateRelevantResponse(llm: ChatOllama, prompt : str, collection : Collection, expandQuery : bool = False, numQueries=5):
    results = []

    if expandQuery:
        queries = expandQuery(llm, prompt, numQueries)
        log(currentLogLevel, INFO_LOG_LEVEL, 'Query expanded')

        for query in queries:
            results.extend(queryTextCollection(collection, query))

    results.extend(queryTextCollection(collection, prompt, 5))
    log(currentLogLevel, INFO_LOG_LEVEL, 'Retrieved documents')
    results = sorted(results, key=lambda x: x['distances'])
    log(currentLogLevel, INFO_LOG_LEVEL, 'Documents sorted by distance')
    results = [result for result in results if [result['ids'] for result in results].count(result['ids']) == 1]
    log(currentLogLevel, INFO_LOG_LEVEL, f'Documents filtered by uniqueness')
    results = [result for result in results if isRelevant(llm, result, prompt)]
    log(currentLogLevel, INFO_LOG_LEVEL, f'Documents filtered by relevance')
    AIMessage = Response(results)
    message = ANSWERPROMPT.format(context=AIMessage.getFormattedContext(), question=prompt)
    response = llm.invoke(message).content
    log(currentLogLevel, INFO_LOG_LEVEL, 'Response generated')
    AIMessage.setResponse(response)

    return AIMessage

def respondtoUser(llm: ChatOllama, user: str, prompt, chatId: str):
    collection = getUserTextCollection(user, chatId)
    response = generateRelevantResponse(llm, prompt, collection)

    return response

def getFirstMessages(user: str, chatId: str):
    with open(f'../users-data/{user}/chats/{chatId}.json') as file:
        messages = load(file)['log']

    userMessage = messages[0]
    AIMessage = messages[1]

    return {'user': userMessage, 'AI': AIMessage}

def getChatTitle(llm: ChatOllama, userMessage: str, AIMessage: str):
    message = TITLECHATPROMPT.format(user=userMessage, AI=AIMessage)
    title = llm.invoke(message).content

    return title

def generateUserChatTitle(llm: ChatOllama, user: str, chatId: str):
    with open(f'./users-data/{user}/info.json') as file:
        userInfo = load(file)

    titles = userInfo['titles']
    firstMessages = getFirstMessages(user, chatId)
    title = getChatTitle(llm, firstMessages['user'], firstMessages['AI'])
    titles[chatId] = title
    userInfo['titles'] = titles

    with open(f'../users-data/{user}/info.json', 'w') as file:
        dump(userInfo, file)

    return title

if __name__ == '__main__':
    # filterwarnings("ignore")
    ChromaClient = PersistentClient(currentDirectory(), Settings(anonymized_telemetry=False))
    log(currentLogLevel, INFO_LOG_LEVEL, 'Client created')
    sentenceTransformer = SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL, trust_remote_code=True)
    log(currentLogLevel, INFO_LOG_LEVEL, 'Embedding function created')
    collection = ChromaClient.get_or_create_collection(name='test-collection', embedding_function=sentenceTransformer)
    log(currentLogLevel, INFO_LOG_LEVEL, 'Collection created')
    addPDFDocument(collection, 'on_the_meaning_of_life_chpt1_coda.pdf')
    log(currentLogLevel, INFO_LOG_LEVEL, f'{collection.count()} Documents in the collection')

    PROMPT = 'What is the meaning of life?'
    llm = ChatOllama(model=MODEL, num_gpu=32)
    response = generateRelevantResponse(llm, PROMPT, collection)
    message = ANSWERPROMPT.format(context=response.getFormattedContext(), question=PROMPT)
    log(currentLogLevel, RESULT_LOG_LEVEL, response)
