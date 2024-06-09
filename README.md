# GPTgram-server
## server structure
<pre>
.  
├── server.py  
├── database.db  
├── LICENSE  
├── .gitignore  
├── requirements.txt  
├── dependencies-utilities  
│   ├── windows  
│   │   └── ...  
│   ├── macOS  
│   │   └── ...  
│   └── linux  
│       └── ...  
├── ollamarag  
│   └── ...  
├── RAG  
│   ├── RAG.py  
│   ├── VectorChromaDB  
│   └── ...  
├── common-data  
│   ├── chroma.sqlite  
│   ├── pdfs  
│   │   └── ...  
│   ├── images  
│   │   └── ...  
│   ├── audios  
│   │   └── ...  
│   └── ...  
└── users-data  
    ├── user1  
    │   ├── chroma.sqlite  
    │   ├── info.json  
    │   └── chats  
    │      ├── chat1
    │      │   ├── log.json
    │      │   ├── pdfs
    │      │   │    └── ...  
    │      │   ├── images
    │      │   │    └── ...  
    │      │   ├── audios
    │      │   │    └── ...  
    │      │   └── ...
    │      ├── ...  
    │      └── chatN  
    ├── ...  
    └── userN   
        └── ...  
</pre>

## Setup
python 3.11 is required (there are some problem of compatibility with python 3.12)
ollama is required
***poppler might be required***

### https setup
#### generate self-signed certificates
```
openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem -subj "/CN=localhost"
```
#### to check certificates
```
openssl x509 -in cert.pem -text -noout
openssl rsa -in key.pem -check 
```
once the server is online go to https://localhost:8765/ and enable not secure content (for self-signed certificates) in the website settings

### Modules needed (manual installation)
- chromadb
- easyocr
- dotenv
- langchain
- langchain-community
- langchain-text-splitters
- numpy
- ollama
- openai
- pdf2image
- pillow
- pypdf
- pytorch (this one need CUDA setup)
- rapidocr-onnxruntime
- sentence
- unstructured
- "unstructured[all-docs]"
- torch (this one need CUDA setup)
- torchaudio (this one need CUDA setup)
- torchvision (this one need CUDA setup)
- transformers
- vt-py
- websockets
 
### Unix/Linux/MacOS

1. Clone the repository:
    ```
    git clone https://github.com/yourusername/GPTgram-server.git
    ```
2. Navigate into the cloned repository:
    ```
    cd GPTgram-server
    ```
3. Create a virtual environment:
    ```
    python3 -m venv ollamarag
    ```
4. Activate the virtual environment:
    ```
    source ollamarag/bin/activate
    ```
5. Install the requirements (listed above)

### Windows

1. Clone the repository:
    ```
    git clone https://github.com/yourusername/GPTgram-server.git
    ```
2. Navigate into the cloned repository:
    ```
    cd GPTgram-server
    ```
3. Create a virtual environment:
    ```
    py -m venv ollamarag
    ```
4. Activate the virtual environment:
    ```
    .\ollamarag\Scripts\activate.ps1
    ```
5. Install the requirements (listed above)

## Incompatibility Note
this cause installation problem
```console
pip install "unstructured[image]"
pip install "unstructured[pdf]"
```

## link interessanti
- https://www.youtube.com/watch?v=2TJxpyO3ei4&ab_channel=pixegami
  - https://github.com/pixegami/rag-tutorial-v2
- https://www.youtube.com/watch?v=oyqNdcbKhew&ab_channel=RobMulla
- https://github.com/tonykipkemboi/ollama_pdf_rag