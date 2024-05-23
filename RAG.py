from chromadb import Client
from chromadb import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain.chat_models.ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.vectorstores.chroma import Chroma
from warnings import filterwarnings

from VectorChromaDB import EMBEDDING_MODEL
from VectorChromaDB import addTextDocument

PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
END = '\033[0m'
MODEL = 'test'

MODEL = 'dolphin-llama3:8b-v2.9-q8_0'

MULTIQUERYPROMPT = PromptTemplate.from_template(
    """You are an AI language model assistant. Your task is to generate five
    different versions of the given user question to retrieve relevant documents from
    a vector database. By generating multiple perspectives on the user question, your
    goal is to help the user overcome some of the limitations of the distance-based
    similarity search. Provide these alternative questions separated by newlines.
    Original question: {question}"""
)

ANSWERPROMPT =  PromptTemplate.from_template(
    """Answer the question based only on the following context:

    {context}

    ---

    Answer the question based on the above context: {question}"""
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

if __name__ == '__main__':
    filterwarnings("ignore")
    ChromaClient = Client(Settings(anonymized_telemetry=False))
    sentenceTransformer = SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL, trust_remote_code=True)
    collection = ChromaClient.create_collection(name='test-collection', embedding_function=sentenceTransformer)

    addTextDocument(collection, 'This is a test document', {'author': 'Marguerite Vasquez'})
    addTextDocument(collection, 'This is another document', {'author': 'Claudia Parker'})
    addTextDocument(collection, "Dolores wouldn't have eaten the meal if she had known", {'author': 'Alan Terry'})
    addTextDocument(collection, 'There were white out conditions in the town', {'author': 'Hulda Lowe'})
    addTextDocument(collection, 'She had the gift of being able to paint songs', {'author': 'Chad Frazier'})

    PROMPT = 'What is the meaning of life?'
    message = MULTIQUERYPROMPT.format(question=PROMPT)
    llm = ChatOllama(model=MODEL, temperature=0.9)
    # multiRetriever = MultiQueryRetriever.from_llm(retriever=CC.as_retriever(), llm=llm, prompt=MULTIQUERYPROMPT)
    # multiRetriever.
    queries = expandQuery(llm, message)

    
