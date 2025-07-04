from warnings import filterwarnings

filterwarnings("ignore", category=DeprecationWarning)
filterwarnings("ignore", category=FutureWarning)

from datetime import datetime
from dateutil.parser import parse
from inspect import currentframe
from json import dump
from json import load
from os import makedirs
from os.path import abspath
from os.path import basename

ERROR_LOG_LEVEL = 0
INFO_LOG_LEVEL = 1
DEBUG_LOG_LEVEL = 2
RESULT_LOG_LEVEL = 3

RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
GREEN = '\033[92m'
GRAY = '\033[90m'
END = '\033[0m'

redText = lambda text: f'{RED}{text}{END}'
yellowText = lambda text: f'{YELLOW}{text}{END}'
cyanText = lambda text: f'{CYAN}{text}{END}'
greenText = lambda text: f'{GREEN}{text}{END}'
grayText = lambda text: f'{GRAY}{text}{END}'

logColor = {
    ERROR_LOG_LEVEL: redText,
    INFO_LOG_LEVEL: greenText,
    DEBUG_LOG_LEVEL: yellowText,
    RESULT_LOG_LEVEL: cyanText
}

logLevel = {
    ERROR_LOG_LEVEL: 'ERROR',
    INFO_LOG_LEVEL: 'INFO',
    DEBUG_LOG_LEVEL: 'DEBUG',
    RESULT_LOG_LEVEL: 'RESULT'
}

def log(currentLogLevel, level, message, parameters: dict = None):
    if currentLogLevel not in logLevel.keys():
        raise ValueError('Invalid log level')
    
    if level > currentLogLevel:
        return

    date = datetime.now().isoformat()
    color = logColor[level]
    type = color(logLevel[level])
    caller = currentframe().f_back.f_code.co_name
    caller = caller if caller != '<module>' else 'main'
    caller = color(caller)
    file = basename(abspath(currentframe().f_back.f_code.co_filename))

    file = color(file)
    message = color(message)
    parameters = f'| {grayText(str(parameters))}' if parameters else None 

    logMessage = f'[{date}][{type}][{file}][{caller}] {message} {parameters if parameters else ""}'

    print(logMessage)

def formatMessage(message: str):
    return message.encode('utf-8').decode('utf-8')

def retrieveTitles(user: str):
    with open(f'./users-data/{user}/info.json') as file:
        data = load(file)
        return data['titles']
    
def retrieveTitlesList(user: str):
    with open(f'./users-data/{user}/info.json') as file:
        data = load(file)['titles']

        titlesList = []

        for hash, title in data.items():
            with open(f'./users-data/{user}/chats/{hash}/log.json') as file:
                creationDate = load(file)['creation_date']
                creationDate = creationDate
                # creationDate = {
                #     'year': creationDate.year, 
                #     'month': creationDate.month, 
                #     'day': creationDate.day, 
                #     'hour': creationDate.hour, 
                #     'minute': creationDate.minute,
                #     'second': creationDate.second
                # }

            titlesList.append({
                'hash': hash,
                'title': title,
                'creation_date': creationDate
            })

        return titlesList

def loadConfig(configPath: str):
    with open(configPath) as file:
        return load(file)