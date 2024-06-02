from warnings import filterwarnings

filterwarnings("ignore", category=DeprecationWarning)
filterwarnings("ignore", category=FutureWarning)

import asyncio
from langchain_community.chat_models.ollama import ChatOllama
import websockets
from json import dumps
from json import loads
from json.decoder import JSONDecodeError
from time import sleep
from Scripts.manage import *
from Scripts.RAG import respondtoUser
from Scripts.RAG import generateUserChatTitle
from Scripts.utils import formatMessage
from Scripts.utils import retrieveTitles
from langchain_community.chat_models.ollama import ChatOllama

TYPE_REGISTER_MESSAGE = "register"           # Tipo di messaggio per la registrazione
TYPE_LOGIN_MESSAGE = "login"                 # Tipo di messaggio per il login
TYPE_CHAT_MESSAGE = "chat";                  # Tipo di messaggio per la chat
TYPE_CHAT_TITLE_MESSAGE = "chatTitle";       # Tipo di messaggio per il titolo della chat
TYPE_MESSAGE_COOKIE = "cookie"               # Tipo di messaggio per i cookie
TYPE_MESSAGE_NEW_COOKIE = "newCookie"        # Tipo di messaggio per i nuovi cookie
TYPE_LOGOUT_MESSAGE = "logout"               # Tipo di messaggio per il logout
TYPE_REQUEST_CHAT_LIST = "chatList"          # Tipo di messaggio per la lista delle chat
TYPE_REQUEST_CHAT = "chatContent"                   # Tipo di messaggio per la chat

MODEL = 'dolphin-llama3:8b-v2.9-q8_0'

currentLogLevel = DEBUG_LOG_LEVEL

# Funzione per gestire messaggi al client
async def handle_message(websocket, data):
    llm = ChatOllama(model=MODEL)
    username = data['user']
    # email = data['email']
    chatID = data['chatId']
    message = formatMessage(data['message'])

    log(currentLogLevel, INFO_LOG_LEVEL, "user message", {'user' : username, 'chatID': chatID, 'message': message})
    
    response = respondtoUser(llm, username, message, chatID)
    responseText = formatMessage(str(response))

    if chatID not in retrieveTitles(username):
        createUserChat(username, chatID)


    echo_message = {
        'typeMessage': TYPE_CHAT_MESSAGE,
        'message': responseText,
    }

    #addTextDocumentToUserCollection(username, message, chatID, 'AI', response)
    addChatTextMessage(username, chatID, message, 'User')
    addChatTextMessage(username, chatID, responseText, 'AI')

    log(currentLogLevel, INFO_LOG_LEVEL, "AI response to user", {'chatID': chatID, 'message': responseText, 'user': username})
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
        await websocket.send(dumps({ 'status': 'error', 'message': 'User already exists' }))
        return
    
    createNewUser(username, email, password, connector)

    # Invia il messaggio di successo al client
    log(currentLogLevel, INFO_LOG_LEVEL, "Registration successful", {'email': email})
    await websocket.send(dumps({'status': 'RegisterSuccess', 'message': 'Registration successful'}))

# Gestione del login
async def handle_login(websocket, data): 
    connector = loadDatabase()
    email = data['email']
    user = getUsername(email, connector)
    log(currentLogLevel, INFO_LOG_LEVEL, "Handling login for", {'email': email})
    if (not doesExists(getUserID(user, email), connector)):
        log(currentLogLevel, ERROR_LOG_LEVEL, "User does not exist", {'email': email})
        await websocket.send(dumps({ 'status': 'error', 'message': 'User does not exist' }))

        return
    
    passwordList = list(data['password'])
    for i in range(len(passwordList)):
        password = passwordList[i]
        if (login(email, password, connector)):
            log(currentLogLevel, INFO_LOG_LEVEL, "Login successful", {'email': email})
            await websocket.send(dumps({ 'status': 'success', 'message': 'Login successful', 'user': user, 'email': email}))
            #TODO reindirizza ora il client alla chat 
            return
        
    log(currentLogLevel, ERROR_LOG_LEVEL, "Wrong password", {'email': email})
    await websocket.send(dumps({ 'status': 'error', 'message': 'Wrong password' }))

    return

# Funzione per gestire il logout
async def logout_handler(websocket, data):
    log(currentLogLevel, DEBUG_LOG_LEVEL, "Handling logout", {'data': data})
    hash = data['hash']
    connector = loadDatabase()
    if checkUserCookie(hash, connector):
        log(currentLogLevel, INFO_LOG_LEVEL, "Logout successful")
        deleteCookie(hash, connector)
        await websocket.send(dumps({ 'status': 'logout', 'message': 'Logout successful', 'hash': hash, 'email': getUserMailFromCookie(hash, connector)}))
        return
    
    log(currentLogLevel, ERROR_LOG_LEVEL, "Logout failed")
    await websocket.send(dumps({ 'status': 'error', 'message': 'Logout failed'}))

# Funzione per gestire i cookie
async def new_login_cookie(websocket, data):
    hash = data['hash']
    username = data['username']
    expire = data['expire']
    connector = loadDatabase()
    
    if checkUserCookie(hash, connector):
        log(currentLogLevel, INFO_LOG_LEVEL, "Cookie already exists")
        return
    
    insertNewCookie(hash, username, expire, connector)
    checkCookies(connector)
    log(currentLogLevel, INFO_LOG_LEVEL, "Cookie table updated")
    email = getUserMailFromCookie(hash, connector)

    await websocket.send(dumps({ 'status': 'NewCookieSuccess', 'message': 'Cookie valid', 'email': email}))

async def login_by_cookie(websocket, data):
    log(currentLogLevel, DEBUG_LOG_LEVEL, "Handling login by cookie", {'data': data})
    hash = data['hash']
    connector = loadDatabase()
    if checkUserCookie(hash, connector):
        log(currentLogLevel, INFO_LOG_LEVEL, "login by cookie successful")
        email = getUserMailFromCookie(hash, connector)
        await websocket.send(dumps({ 'status': 'CookieSuccess', 'message': 'Cookie valid', 'email': email}))
        return
    
    log(currentLogLevel, ERROR_LOG_LEVEL, "login by cookie failed")
    await websocket.send(dumps({ 'status': 'error', 'message': 'Cookie invalid'}))

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

async def handle_chat_list(websocket, data):
    username = data['user']
    titles = retrieveTitlesList(username)
    message = {
        'typeMessage': TYPE_REQUEST_CHAT_LIST,
        'titles': titles
    }

    #log(currentLogLevel, DEBUG_LOG_LEVEL, "chat list request", {'titles': titles})

    await websocket.send(dumps(message))

async def handle_chat_request(websocket, data):
    username = data['user']
    chatID = data['chatId']
    messages = getChatMessages(username, chatID)
    message = {
        'typeMessage': TYPE_REQUEST_CHAT,
        'messages': messages,
        'chatID': chatID,
    }

    log(currentLogLevel, INFO_LOG_LEVEL, "chat request", {'chatID': chatID, 'user': username})

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
                elif data['typeMessage'] == TYPE_MESSAGE_COOKIE:
                    await login_by_cookie(websocket, data)
                elif data['typeMessage'] == TYPE_MESSAGE_NEW_COOKIE:
                    await new_login_cookie(websocket, data)
                elif data['typeMessage'] == TYPE_LOGOUT_MESSAGE:
                    await logout_handler(websocket, data)
                elif data['typeMessage'] == TYPE_REQUEST_CHAT_LIST:
                    await handle_chat_list(websocket, data)
                elif data['typeMessage'] == TYPE_REQUEST_CHAT:
                    await handle_chat_request(websocket, data)
                else:
                    print(f"Unknown message type: {data['typeMessage']}")
            except JSONDecodeError as e:
                log(currentLogLevel, ERROR_LOG_LEVEL, "Invalid JSON", {'message': e})

#TODO: adesso la chat viene ricreata dobiamo procedare da qui: gestire messagi audio e possibilmente file in generale e fixare gli audio per farli responsivi
if __name__ == "__main__":
    filterwarnings("ignore", category=DeprecationWarning)
    filterwarnings("ignore", category=FutureWarning)
    connector = loadDatabase()
    deleteAllData(connector)
    connector = loadDatabase()
    setupData()
    checkCookies(connector)
    log(currentLogLevel, INFO_LOG_LEVEL, "Starting server")
    start_server = websockets.serve(handler, "localhost", 8765)
    log(currentLogLevel, INFO_LOG_LEVEL, "Server started")
    asyncio.get_event_loop().run_until_complete(start_server)
    log(currentLogLevel, INFO_LOG_LEVEL, "event loop started")
    asyncio.get_event_loop().run_forever()