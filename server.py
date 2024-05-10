import asyncio
import websockets
import json
import hashlib
import os
import binascii
import sys
import base64

TYPE_REGISTER_MESSAGE = "register"  # Tipo di messaggio per la registrazione
TYPE_LOGIN_MESSAGE = "login"        # Tipo di messaggio per il login
TYPE_CHAT_MESSAGE = "chat";     # Tipo di messaggio per la chat
CLIENTS_FILE = 'clients.json'       # File per memorizzare i dati dei client



# Dizionario per memorizzare le email e le password dei client
clients = {}


# Salva i dati dei client alla chiusura del server
def save_clients():
    if not os.path.exists(CLIENTS_FILE):
        with open(CLIENTS_FILE, 'w') as f:
            pass
    with open(CLIENTS_FILE, 'w') as f:
        json.dump(clients, f)

# Carica i dati dei client all'avvio del server
if os.path.exists(CLIENTS_FILE) and os.path.getsize(CLIENTS_FILE) > 0:
    with open(CLIENTS_FILE, 'r') as f:
        try:
            clients = json.load(f)
        except json.JSONDecodeError:
            print("Error decoding JSON from file")
            sys.exit(1)


# Funzione per gestire messaggi al client
async def handle_message(websocket, data):
    echo_message = {
        'typeMessage': TYPE_CHAT_MESSAGE,
        'message': f"Echo: {data['message']}"
    }
    # Invia il messaggio di echo al client
    await websocket.send(json.dumps(echo_message))
    

#registrazione clients
async def handle_register(websocket, data):
    # Gestisci la registrazione qui...
    print(f"Handling register for {data['email']}")
    email = data['email']
    if (email in clients):
        print(f"Email {email} already registered")
        await websocket.send(json.dumps({
            'status': 'error',
            'message': 'Email already registered'
        }))
        return
    password = data['password']
    # Crea un sale
    salt = os.urandom(32)
    # Crea un hash della password con il sale
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    # Memorizza il sale e l'hash della password
    clients[email] = {
        'salt': base64.b64encode(salt).decode('utf-8'),
        'key': base64.b64encode(key).decode('utf-8')
    }
    # Crea un messaggio di successo
    success_message = {
        'status': 'success',
        'message': 'Registration successful'
    }
    # Invia il messaggio di successo al client
    save_clients()
    await websocket.send(json.dumps(success_message))


# Gestione del login

async def handle_login(websocket, data): 
    print(f"Handling login for {data['email']}") 
    email = data['email'] 
    if (email not in clients): 
        print(f"Email {email} not registered") 
        await websocket.send(json.dumps({ 'status': 'error', 'message': 'Email not registered' })) 
        return 
    password = data['password'] 
    salt = clients[email]['salt']
    print(f"Salt before decoding: {salt}")
    try:
        salt = base64.b64decode(salt)
    except binascii.Error as e:
        print(f"Error decoding salt: {e}")
        return
    print(f"Salt after decoding: {salt}")
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    stored_key = base64.b64decode(clients[email]['key'])
    if (key == stored_key): 
        print(f"Login successful for {email}") 
        await websocket.send(json.dumps({ 'status': 'success', 'message': 'Login successful' })) 
    else: 
        print(f"Login failed for {email}") 
        await websocket.send(json.dumps({ 'status': 'error', 'message': 'Login failed' })) 
    #adesso mandare al client qualcosa che faccia in modo di passare alla pagina di chat



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
                print(f"Received a message that's not valid JSON: {message}")

start_server = websockets.serve(handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()