from warnings import filterwarnings

filterwarnings("ignore", category=DeprecationWarning)
filterwarnings("ignore", category=FutureWarning)

import asyncio
from langchain_community.chat_models.ollama import ChatOllama
import websockets
from json import dumps
from json import loads
from time import sleep
from Scripts.manage import *
from Scripts.RAG import respondtoUser
from Scripts.VectorChromaDB import addTextDocumentToUserCollection
from Scripts.RAG import generateUserChatTitle
from Scripts.utils import retrieveTitles
from langchain_community.chat_models.ollama import ChatOllama

TYPE_REGISTER_MESSAGE = "register"           # Tipo di messaggio per la registrazione
TYPE_LOGIN_MESSAGE = "login"                 # Tipo di messaggio per il login
TYPE_CHAT_MESSAGE = "chat";                  # Tipo di messaggio per la chat
TYPE_CHAT_TITLE_MESSAGE = "chatTitle";       # Tipo di messaggio per il titolo della chat

MODEL = 'dolphin-llama3:8b-v2.9-q8_0'

currentLogLevel = DEBUG_LOG_LEVEL

# Funzione per gestire messaggi al client
async def handle_message(websocket, data):
    llm = ChatOllama(model=MODEL)
    username = data['user']
    # email = data['email']
    chatID = data['chatId']
    message = data['message']

    log(currentLogLevel, INFO_LOG_LEVEL, "user message", {'user' : username, 'chatID': chatID, 'message': message})
    
    response = respondtoUser(llm, username, message, chatID)

    if chatID not in retrieveTitles(username):
        createUserChat(username, chatID)


    echo_message = {
        'typeMessage': TYPE_CHAT_MESSAGE,
        'message': response.getText(),
    }

    #addTextDocumentToUserCollection(username, message, chatID, 'AI', response)
    addChatTextMessage(username, chatID, message, 'User')
    addChatTextMessage(username, chatID, response.getText(), 'AI')

    log(currentLogLevel, INFO_LOG_LEVEL, "AI response to user", {'chatID': chatID, 'message': response.getText(), 'user': username})
    await websocket.send(dumps(echo_message))
    

#registrazione clients
async def handle_register(websocket, data):
    # RACCOLTA DATI
    log(currentLogLevel, INFO_LOG_LEVEL, "Handling registration for", {'email': data['email']})
    username = data['username']
    email = data['email']
    password = data['password']

    #controllo se l'email è già stata registrata
    connector = loadDatabase()
    userID = getUserID(username, email)
    if (doesExists(userID, connector )):
        log(currentLogLevel, ERROR_LOG_LEVEL, "User already exists", {'email': email})
        await websocket.send(json.dumps({ 'status': 'error', 'message': 'User already exists' }))
        return
    
    createNewUser(username, email, password, connector)

    # Invia il messaggio di successo al client
    log(currentLogLevel, INFO_LOG_LEVEL, "Registration successful", {'email': email})
    await websocket.send(dumps({'status': 'success', 'message': 'Registration successful'}))


# Gestione del login
async def handle_login(websocket, data): 
    connector = loadDatabase()
    email = data['email']
    user = getUsername(email, connector)
    log(currentLogLevel, INFO_LOG_LEVEL, "Handling login for", {'email': email})
    if (not doesExists(getUserID(user, email), connector)):
        log(currentLogLevel, ERROR_LOG_LEVEL, "User does not exist", {'email': email})
        await websocket.send(json.dumps({ 'status': 'error', 'message': 'User does not exist' }))

        return
    
    passwordList = list(data['password'])
    for i in range(len(passwordList)):
        password = passwordList[i]
        if (login(email, password, connector)):
            log(currentLogLevel, INFO_LOG_LEVEL, "Login successful", {'email': email})
            await websocket.send(json.dumps({ 'status': 'success', 'message': 'Login successful' }))
            #TODO reindirizza ora il client alla chat 
            return
        
    log(currentLogLevel, ERROR_LOG_LEVEL, "Wrong password", {'email': email})
    await websocket.send(json.dumps({ 'status': 'error', 'message': 'Wrong password' }))

    return

async def handle_title(websocket, data):

    llm = ChatOllama(model=MODEL)
    username = data['user']
    chatID = data['chatId']
    title = generateUserChatTitle(llm, username, chatID)
    message = {
        'typeMessage': TYPE_CHAT_TITLE_MESSAGE,
        'title': title
    }

    log(currentLogLevel, INFO_LOG_LEVEL, "AI response to user", {'chatID': chatID, 'message': title, 'user': username}) 
    saveChatTitle(username, chatID, title)
    log(currentLogLevel, INFO_LOG_LEVEL, "Chat title saved", {'chatID': chatID, 'title': title, 'user': username})
    
    await websocket.send(dumps(message))

# Funzione per gestire i messaggi
async def handler(websocket, path):
    async for message in websocket:
        if message:
            try:
                data = loads(message)
                if data['typeMessage'] == TYPE_REGISTER_MESSAGE:
                    await handle_register(websocket,data)
                elif data['typeMessage'] == TYPE_LOGIN_MESSAGE:
                    await handle_login(websocket, data)
                elif data['typeMessage'] == TYPE_CHAT_MESSAGE:
                    await handle_message(websocket, data)
                elif data['typeMessage'] == TYPE_CHAT_TITLE_MESSAGE:
                    await handle_title(websocket, data)
                else:
                    print(f"Unknown message type: {data['typeMessage']}")
            except json.JSONDecodeError as e:
                log(currentLogLevel, ERROR_LOG_LEVEL, "Invalid JSON", {'message': e})


if __name__ == "__main__":
    filterwarnings("ignore", category=DeprecationWarning)
    filterwarnings("ignore", category=FutureWarning)
    log(currentLogLevel, INFO_LOG_LEVEL, "Starting server")
    start_server = websockets.serve(handler, "localhost", 8765)
    log(currentLogLevel, INFO_LOG_LEVEL, "Server started")
    asyncio.get_event_loop().run_until_complete(start_server)
    log(currentLogLevel, INFO_LOG_LEVEL, "event loop started")
    asyncio.get_event_loop().run_forever()