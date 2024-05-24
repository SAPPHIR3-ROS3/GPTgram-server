from dotenv import load_dotenv
from os import getenv
from vt import Client

MB = 1024 * 1024

def isMalicious(filepath):
    file = open(filepath, 'rb')
    
    with Client(getenv('VIRUSTOTAL_API_KEY')) as client:
        analysis = client.scan_file(file, wait_for_completion=True)
        results = analysis.results
        
        for antivirus in results:
            if results[antivirus]['category'] == 'malicious':
                return True
        
        return False
    
def howMaliciousIs(filepath):
    file = open(filepath, 'rb')

    with Client(getenv('VIRUSTOTAL_API_KEY')) as client:
        analysis = client.scan_file(file, wait_for_completion=True)
        results = analysis.results
        antivirusCount = len(results)
        maliciousCount = 0
        unsupportedCount = 0
        
        for antivirus in results:
            if results[antivirus]['category'] == 'malicious':
                maliciousCount += 1
            elif results[antivirus]['category'] == 'type-unsupported':
                unsupportedCount += 1
    
    return maliciousCount / (antivirusCount - unsupportedCount)
        
if __name__ == '__main__':
    load_dotenv()
    filepath = 'virustest.7z'
    file = open(filepath, 'rb')
    

    print(isMalicious(filepath))
