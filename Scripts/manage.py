from warnings import filterwarnings

filterwarnings("ignore", category=DeprecationWarning)
filterwarnings("ignore", category=FutureWarning)

from datetime import datetime
from dateutil.parser import parse
from json import dump
from json import load
from hashlib import sha1 as SHA1
from hashlib import sha256 as SHA256
from os import makedirs
from os import remove
from os import rmdir
from os.path import dirname
from os.path import exists
from shutil import rmtree
from sqlite3 import connect

from Scripts.utils import *
from Scripts.VectorChromaDB import addTextDocumentToUserCollection
from Scripts.VectorChromaDB import addPDFDocumentToUserCollection
from Scripts.VectorChromaDB import getID

DBPATH = 'database.db'
USERSDATAPATH = 'users-data'

currentLogLevel = INFO_LOG_LEVEL

def getUserID(username: str, email: str):
    IDText = f'{email}{username}'.encode('utf-8')
    IDHash = SHA256(IDText).hexdigest().upper()

    return IDHash

def getUsername(email: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT name FROM users WHERE email = :email", {'email': email})
        user = cursor.fetchone()

        if user is not None:
            return user[0]

        return user

def getUserEmail(username: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT email FROM users WHERE name = :name", {'name': username})
        email = cursor.fetchone()[0]

        return email

def getMetadata(document: str, sender : str, data = None, uri : str = None):
    metadata = dict()
    metadata['date'] = datetime.now().isoformat()
    metadata['author'] = sender
    metadata['uri'] = uri
    if uri is not None:
        metadata['type'] = uri.split('.')[-1]
    metadata['data'] = data if data is not None else 'None'

    return metadata

def doesExists(userID: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT * FROM users WHERE id = :id", {'id': userID})
        user = cursor.fetchone()
    
        return user is not None

def isEmailRegistered(email: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT * FROM users WHERE email = :email", {'email': email})
        user = cursor.fetchone()
    
        return user is not None
    
def isUsernameRegistered(username: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT * FROM users WHERE name = :name", {'name': username})
        user = cursor.fetchone()
    
        return user is not None

def createNewUser(user: str, email: str, passwordHash: str,  connector: connect):
    if not doesExists(getUserID(user, email), connector):
        with connector:
            cursor = connector.cursor()
            creationDate = datetime.now().isoformat()
            userID = getUserID(user, email)
            cursor.execute("INSERT INTO users (id, name, email, password_hash, created_at) VALUES (:id, :name, :email, :password_hash, :created_at)", 
                {'id': userID, 'name': user, 'email': email, 'password_hash': passwordHash, 'created_at': creationDate}
            )

            log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} created')

        userPath = f'users-data/{user}'
        userChatsPath = f'{userPath}/chats'

        makedirs(userPath)
        makedirs(userChatsPath)

        log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} directories created')

        info = {'user': user, 'email': email, 'created_at': creationDate, 'id': userID, 'titles': dict()}

        with open(f'{userPath}/info.json', 'w') as file:
            dump(info, file)

        return True

    else: return False

def modifyUser(userID: str, user: str, connector: connect, email: str = None, passwordHash: str = None):
    if doesExists(userID, connector):
        with connector:
            cursor = connector.cursor()

            if email is not None:
                userID = getUserID(user, email)
                cursor.execute("UPDATE users SET email = :email WHERE id = :id", 
                    {'email': email, 'id': userID}
                )
                log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} email updated')
            
            if passwordHash is None:
                cursor.execute("UPDATE users SET password_hash = :password_hash WHERE id = :id", 
                    {'password_hash': passwordHash, 'id': userID}
                )
                log(currentLogLevel, INFO_LOG_LEVEL, f'User {user} password updated')

        return True
    
    else: return False

def doesUserChatExists(user: str, chatID: str):
    return exists(f'./users-data/{user}/chats/{chatID}')

def createUserChat(user: str, chatID: str):
    if doesUserChatExists(user, chatID):
        log(currentLogLevel, ERROR_LOG_LEVEL, 'User chat already exists', {'user': user, 'chat_id': chatID})
        return False
    
    userPath = f'users-data/{user}'
    userChatPath = f'{userPath}/chats/{chatID}'
    userChatPDFsPath = f'{userChatPath}/pdfs'
    userChatImagesPath = f'{userChatPath}/images'
    userChatAudiosPath = f'{userChatPath}/audios'

    makedirs(userChatPath, exist_ok=True)
    makedirs(userChatPDFsPath, exist_ok=True)
    makedirs(userChatImagesPath, exist_ok=True)
    makedirs(userChatAudiosPath, exist_ok=True)

    log(currentLogLevel, INFO_LOG_LEVEL, 'User chat created', {'user': user, 'chat_id': chatID})

    logFile = {'log': [], 'creation_date': datetime.now().isoformat(),  'chat_id': chatID, 'user': user}
    with open(f'{userChatPath}/log.json', 'w') as file:
        dump(logFile, file)

    return True

def hasChatTitle(user: str, chatID: str):
    if not doesUserChatExists(user, chatID):
        log(currentLogLevel, ERROR_LOG_LEVEL, 'User chat does not exists', {'user': user, 'chat_id': chatID})
        return False

    userInfoPath = f'./users-data/{user}/info.json'
    with open(userInfoPath, 'r') as file:
        info = load(file)

    return chatID in info['titles']

def saveChatTitle(user: str, chatID: str, title: str):
    if not doesUserChatExists(user, chatID):
        log(currentLogLevel, ERROR_LOG_LEVEL, 'User chat does not exists', {'user': user, 'chat_id': chatID})
        return False

    if hasChatTitle(user, chatID):
        return False

    userInfoPath = f'./users-data/{user}/info.json'
    with open(userInfoPath, 'r') as file:
        info = load(file)
        info['titles'][chatID] = title 

    with open(userInfoPath, 'w') as file:
        dump(info, file)
    
    log(currentLogLevel, INFO_LOG_LEVEL, 'Chat title saved', {'user': user, 'chat_id': chatID, 'title': title})

    return True

def addChatTextMessage(user: str, chatID: str, message: str, sender: str):
    if not doesUserChatExists(user, chatID):
        log(currentLogLevel, ERROR_LOG_LEVEL, 'User chat does not exists', {'user': user, 'chat_id': chatID})
        return False
    
    userChatPath = f'./users-data/{user}/chats/{chatID}'
    with open(f'{userChatPath}/log.json', 'r') as file:
        logFile = load(file)

    metadata = getMetadata(message, sender)
    messageItem = {'message': message, 'sender': sender, 'date': datetime.now().isoformat(), 'type': 'text', 'location': '', 'id': getID(message, metadata)}
    logFile['log'].append(messageItem)

    with open(f'{userChatPath}/log.json', 'w') as file:
        dump(logFile, file)
    
    log(currentLogLevel, INFO_LOG_LEVEL, 'Text message added', {'user': user, 'chat_id': chatID, 'message': message, 'sender': sender})

    addTextDocumentToUserCollection(user, chatID, message, sender)

    return True

def addChatAudioMessage(user: str, chatID: str, transcription: str, location: str, sender: str):
    if not doesUserChatExists(user, chatID):
        log(currentLogLevel, ERROR_LOG_LEVEL, 'User chat does not exists', {'user': user, 'chat_id': chatID})
        return False
    
    userChatPath = f'./users-data/{user}/chats/{chatID}'
    with open(f'{userChatPath}/log.json', 'r') as file:
        logFile = load(file)

    metadata = getMetadata(transcription, sender, uri=location)
    messageItem = {'message': transcription, 'sender': sender, 'date': datetime.now().isoformat(), 'type': 'audio', 'location': location, 'id': getID(transcription, metadata)}
    logFile['log'].append(messageItem)

    with open(f'{userChatPath}/log.json', 'w') as file:
        dump(logFile, file)
    
    log(currentLogLevel, DEBUG_LOG_LEVEL, 'Audio message added', {'user': user, 'chat_id': chatID, 'message': transcription, 'sender': sender, 'location': location})

    #addAudioDocumentToUserCollection(user, chatID, transcription, sender, location)
    addTextDocumentToUserCollection(user, chatID, transcription, sender, metadata) #TODO: add native implentation not a siply the trascription

    return True

def addChatPDFMessage(user: str, chatID: str, location: str, sender: str):
    if not doesUserChatExists(user, chatID):
        log(currentLogLevel, ERROR_LOG_LEVEL, 'User chat does not exists', {'user': user, 'chat_id': chatID})
        return False
    
    userChatPath = f'./users-data/{user}/chats/{chatID}'
    with open(f'{userChatPath}/log.json', 'r') as file:
        logFile = load(file)

    metadata = getMetadata(location, sender, uri=location)
    messageItem = {'message': location, 'sender': sender, 'date': datetime.now().isoformat(), 'type': 'pdf', 'location': location, 'id': getID(location, metadata, uri=location)}
    logFile['log'].append(messageItem)

    with open(f'{userChatPath}/log.json', 'w') as file:
        dump(logFile, file)
    
    log(currentLogLevel, INFO_LOG_LEVEL, 'PDF message added', {'user': user, 'chat_id': chatID, 'message': location, 'sender': sender, 'location': location})

    addPDFDocumentToUserCollection(user, chatID, location, metadata, sender, metadata)

    return True

def deleteUserChat(user: str, chatID: str):
    if exists(f'users-data/{user}/chats/{chatID}'):
        rmtree(f'users-data/{user}/chats/{chatID}')
        log(currentLogLevel, INFO_LOG_LEVEL, 'User chat deleted', {'user': user, 'chat_id': chatID})

        return True
    
    else: return False

def deleteUser(userID: str, connector: connect):
    if doesExists(userID, connector):
        with connector:
            cursor = connector.cursor()
            cursor.execute("DELETE FROM users WHERE id = :id", {'id': userID})
            log(currentLogLevel, INFO_LOG_LEVEL, f'User {userID} deleted')
            
        userPath = f'users-data/{userID}'
        rmtree(userPath)
        log(currentLogLevel, INFO_LOG_LEVEL, f'User {userID} data deleted')

        return True
    
    else: return False

def login(email: str, passwordHash: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT * FROM users WHERE email = :email AND password_hash = :password_hash", {'email': email, 'password_hash': passwordHash})
        user = cursor.fetchone()

        if user is not None:
            return True
        
        else: return False

def createCommonData():
    if not exists('common-data'):
        makedirs('common-data')
        makedirs('common-data/websites')
        makedirs('common-data/pdfs')
        makedirs('common-data/images')
        makedirs('common-data/audios')

        log(currentLogLevel, INFO_LOG_LEVEL, 'Common data directories created')

def deleteCommonData(confirm: bool = False):
    if confirm:
        rmtree('common-data')
        log(currentLogLevel, INFO_LOG_LEVEL, 'Common data deleted')

def loadDatabase():
    dirpath = dirname(DBPATH)
    if not exists(DBPATH):
        if len(dirpath) > 0:
            makedirs(dirpath)

        with connect(DBPATH) as connector:
            cursor = connector.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT NOT NULL PRIMARY KEY, 
                    name TEXT NOT NULL UNIQUE, 
                    email TEXT NOT NULL UNIQUE, 
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                    )
                ''')
            connector.commit()
            log(currentLogLevel, INFO_LOG_LEVEL, 'users table created')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cookies (
                    id TEXT NOT NULL PRIMARY KEY, 
                    user TEXT NOT NULL, 
                    expire TEXT NOT NULL
                    )
                ''')
            connector.commit()
            log(currentLogLevel, INFO_LOG_LEVEL, 'cookies table created')

    if not exists(USERSDATAPATH):
        makedirs(USERSDATAPATH)

    if not exists('common-data'):
        createCommonData()
    
    connector = connect(DBPATH)

    return connector

def insertNewCookie(hash: str, user: str, expire: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("INSERT INTO cookies (id, user, expire) VALUES (:id, :user, :expire)", 
            {'id': hash, 'user': user, 'expire': expire}
        )
        connector.commit()
        log(currentLogLevel, INFO_LOG_LEVEL, 'Cookie inserted')

def checkUserCookie(hash: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT * FROM cookies WHERE id = :id", {'id': hash})
        cookie = cursor.fetchone()

        return cookie is not None

def getUserMailFromCookie(hash: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT user FROM cookies WHERE id = :id", {'id': hash})
        user = cursor.fetchone()[0]


        return getUserEmail(user, connector)

def deleteCookie(hash: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("DELETE FROM cookies WHERE id = :id", {'id': hash})
        connector.commit()
        log(currentLogLevel, INFO_LOG_LEVEL, 'Cookie deleted')

def checkCookies(connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT * FROM cookies")
        cookies = cursor.fetchall()

        expiredCookies = []
        for cookie in cookies:
            if datetime.now() > parse(cookie[2]):
                expiredCookies.append(cookie[0])
        
        for cookie in expiredCookies:
            cursor.execute("DELETE FROM cookies WHERE id = :id", {'id': cookie})
            connector.commit()

        log(currentLogLevel, INFO_LOG_LEVEL, 'Outdated cookies deleted')

def doesChatExists(user: str, chatID: str):
    return exists(f'./users-data/{user}/chats/{chatID}')

def getChatMessages(user: str, chatID: str):
    if not doesUserChatExists(user, chatID):
        log(currentLogLevel, ERROR_LOG_LEVEL, 'User chat does not exists', {'user': user, 'chat_id': chatID})

        return False

    if not doesChatExists(user, chatID):
        log(currentLogLevel, ERROR_LOG_LEVEL, 'Chat does not exists', {'user': user, 'chat_id': chatID})

        return False
    
    with open(f'./users-data/{user}/chats/{chatID}/log.json', 'r') as file:
        chatLog = load(file)['log']
        log(currentLogLevel, INFO_LOG_LEVEL, 'Chat messages retrieved', {'user': user, 'chat_id': chatID})
        

        return chatLog
    
def createUsersData():
    if not exists(USERSDATAPATH):
        makedirs(USERSDATAPATH)
        log(currentLogLevel, INFO_LOG_LEVEL, 'Users data directories created')

        return True
    
    else: return False

def deleteUsersData(connector: connect, confirm: bool = False):
    if confirm:
        rmtree(USERSDATAPATH)
        log(currentLogLevel, INFO_LOG_LEVEL, 'Users data deleted')

        with connector:
            cursor = connector.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            for table in tables:
                cursor.execute(f"DROP TABLE {table[0]}")
                connector.commit()

            log(currentLogLevel, INFO_LOG_LEVEL, 'Database deleted')
            
        connector.close()
        remove(DBPATH)
        log(currentLogLevel, INFO_LOG_LEVEL, 'Database file deleted')

def setupData():
    createUsersData()
    createCommonData()
    log(currentLogLevel, INFO_LOG_LEVEL, 'Data setup completed')

    return loadDatabase()

def deleteAllData(connector: connect, confirm : bool = False):
    if confirm and input('Are you sure you want to delete all data? (y/n) ').lower() == 'y':
        deleteUsersData(connector, confirm)
        deleteCommonData(confirm)
        log(currentLogLevel, INFO_LOG_LEVEL, 'All data deleted')
        