from datetime import datetime

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

    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    color = logColor[level]
    type = color(logLevel[level])
    message = color(message)
    parameters = f'| {grayText(str(parameters))}' if parameters else None 

    logMessage = f'[{date}][{type}] {message} {parameters if parameters else ""}'

    print(logMessage)
