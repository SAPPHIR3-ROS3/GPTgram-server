import asyncio
from langchain_community.chat_models.ollama import ChatOllama
import websockets
import json
from time import sleep
from Scripts.manage import *
from Scripts.RAG import respondtoUser
from Scripts.VectorChromaDB import addTextDocumentToUserCollection

TYPE_REGISTER_MESSAGE = "register"  # Tipo di messaggio per la registrazione
TYPE_LOGIN_MESSAGE = "login"        # Tipo di messaggio per il login
TYPE_CHAT_MESSAGE = "chat";     # Tipo di messaggio per la chat

currentLogLevel = INFO_LOG_LEVEL

# Funzione per gestire messaggi al client
async def handle_message(websocket, data):
    llm = ChatOllama()
    username = data['user']
    # email = data['email']
    chatID = data['chatID']
    message = data['message']
    
    response = respondtoUser(llm, username, message, chatID)

    echo_message = {
        'typeMessage': TYPE_CHAT_MESSAGE,
        'message': str(response),
    }
    # Invia il messaggio di echo al client
    # sleep(2) # TODO: Rimuovere questa riga
    log(currentLogLevel, INFO_LOG_LEVEL, "Echoing message", {'message': data['message']})
    await websocket.send(json.dumps(echo_message))
    

#registrazione clients
async def handle_register(websocket, data):
    # RACCOLTA DATI
    log(currentLogLevel, INFO_LOG_LEVEL, "Handling registration for", {'email': data['email']})
    username = data['username']
    email = data['email']
    password = str(data['password'])

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
    await websocket.send(json.dumps({'status': 'success', 'message': 'Registration successful'}))


# Gestione del login
async def handle_login(websocket, data): 
    connector = loadDatabase()
    email = data['email']
    log(currentLogLevel, INFO_LOG_LEVEL, "Handling login for", {'email': email})
    if (not doesExists(getUserID("", email), connector)):
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

# Funzione per gestire i messaggi
async def handler(websocket, path):
    async for message in websocket:
        if message:
            try:
                data = json.loads(message)
                if data['typeMessage'] == TYPE_REGISTER_MESSAGE:
                    await handle_register(websocket,data)
                elif data['typeMessage'] == TYPE_LOGIN_MESSAGE:
                    await handle_login(websocket, data)
                elif data['typeMessage'] == TYPE_CHAT_MESSAGE:
                    await handle_message(websocket, data)
                else:
                    print(f"Unknown message type: {data['typeMessage']}")
            except json.JSONDecodeError:
                log(currentLogLevel, ERROR_LOG_LEVEL, "Invalid JSON", {'message': message})

start_server = websockets.serve(handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()