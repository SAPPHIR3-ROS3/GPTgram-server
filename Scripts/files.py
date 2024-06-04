from warnings import filterwarnings

filterwarnings("ignore", category=DeprecationWarning)
filterwarnings("ignore", category=FutureWarning)
filterwarnings("ignore", category=UserWarning)

from Scripts.utils import formatMessage
from Scripts.utils import DEBUG_LOG_LEVEL
from Scripts.utils import ERROR_LOG_LEVEL
from Scripts.utils import INFO_LOG_LEVEL
from Scripts.utils import log

currentLogLevel = DEBUG_LOG_LEVEL

def convertFileBlobtoPDF(blob: bytes, user: str, chatId: str, fileName: str):
    filePath = f'./users-data/{user}/chats/{chatId}/pdfs/'
    filePath += f'{fileName}'

    with open(filePath, 'wb') as file:
        file.write(blob)

    log(currentLogLevel, INFO_LOG_LEVEL, 'file saved to', {'filePath': filePath})

    return filePath