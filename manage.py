from datetime import datetime
from hashlib import sha256 as SHA256
from os import makedirs
from os import remove
from os import rmdir
from os.path import dirname
from os.path import exists
from shutil import rmtree
from sqlite3 import connect

DBPATH = 'database.db'
USERSDATAPATH = 'users-data'

def getUserID(username: str, email: str):
    IDText = f'{email}{username}'.encode('utf-8')
    IDHash = SHA256(IDText).hexdigest().upper()

    return IDHash

def doesExists(userID: str, connector: connect):
    with connector:
        cursor = connector.cursor()
        cursor.execute("SELECT * FROM users WHERE id = :id", {'id': userID})
        user = cursor.fetchone()
    
        return user is not None

def createNewUser(user: str, email: str, passwordHash: str,  connector: connect):
    if not doesExists(user, email, connector):
        with connector:
            cursor = connector.cursor()
            creationDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            userID = getUserID(user, email)
            cursor.execute("INSERT INTO users (id, name, email, password_hash, created_at) VALUES (:id, :name, :email, :password_hash, :created_at)", 
                {'id': userID, 'name': user, 'email': email, 'password_hash': passwordHash, 'created_at': creationDate}
            )

        userPath = f'users-data/{user}'
        userChatsPath = f'{userPath}/chats'
        userPDFPath = f'{userPath}/pdfs'
        userPPTXPath = f'{userPath}/pptxs'
        userCSVPath = f'{userPath}/csvs'
        userImagesPath = f'{userPath}/images'
        userAudiosPath = f'{userPath}/audios'

        makedirs(userPath)
        makedirs(userChatsPath)
        makedirs(userCSVPath)
        makedirs(userPDFPath)
        makedirs(userPPTXPath)
        makedirs(userImagesPath)
        makedirs(userAudiosPath)
        
        return True

    else: return False

def modifyUser(userID: str, connector: connect, email: str = None, passwordHash: str = None):
    if doesExists(userID, connector):
        with connector:
            cursor = connector.cursor()

            if email is not None:
                cursor.execute("UPDATE users SET email = :email WHERE id = :id", 
                    {'email': email, 'id': userID}
                )
            
            if passwordHash is None:
                cursor.execute("UPDATE users SET password_hash = :password_hash WHERE id = :id", 
                    {'password_hash': passwordHash, 'id': userID}
                )

        return True
    
    else: return False

def deleteUser(userID: str, connector: connect):
    if doesExists(userID, connector):
        with connector:
            cursor = connector.cursor()
            cursor.execute("DELETE FROM users WHERE id = :id", {'id': userID})
            
        userPath = f'users-data/{userID}'
        rmtree(userPath)

        return True
    
    else: return False

def createCommonData():
    if not exists('common-data'):
        makedirs('common-data')
        makedirs('common-data/websites')
        makedirs('common-data/pdfs')
        makedirs('common-data/images')
        makedirs('common-data/audios')

def deleteCommonData(confirm: bool = False):
    if confirm:
        rmtree('common-data')

def loadDatabase():
    dirpath = dirname(DBPATH)
    if not exists(DBPATH):
        if len(dirpath) > 0:
            makedirs(dirpath)

        with connect(DBPATH) as connector:
            cursor = connector.cursor()
            cursor.execute('''
                CREATE TABLE users (
                    id TEXT NOT NULL PRIMARY KEY, 
                    name TEXT NOT NULL, 
                    email TEXT NOT NULL, 
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                    )
                ''')
            cursor.commit()

    if not exists(USERSDATAPATH):
        makedirs(USERSDATAPATH)

    if not exists('common-data'):
        createCommonData()
    
    connector = connect(DBPATH)

    return connector

def deleteUsersData(connector: connect, confirm: bool = False):
    if confirm:
        rmtree(USERSDATAPATH)

        with connector:
            cursor = connector.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            for table in tables:
                cursor.execute(f"DROP TABLE {table[0]}")
                cursor.commit()
            
        connector.close()
        remove(DBPATH)

def deleteAllData(connector: connect, confirm: bool = False):
    if confirm:
        deleteUsersData(connector, confirm)
        deleteCommonData(confirm)