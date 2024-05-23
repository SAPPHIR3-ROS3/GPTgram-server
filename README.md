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
    │   ├── chats  
    │   │   ├── chat1  
    │   │   ├── ...  
    │   │   └── chatN  
    │   ├── pdfs  
    │   │   └── ...  
    │   ├── images  
    │   │   └── ...  
    │   ├── audios  
    │   │   └── ...  
    │   └── ...  
    ├── ...  
    └── userN  
        ├── chroma.sqlite
        ├── info.json
        ├── chats
        │   ├── chat1
        │   ├── ...
        │   └── chatN
        ├── pdfs  
        │   └── ...  
        ├── images  
        │   └── ...  
        ├── audios  
        │   └── ...  
        └── ...  
</pre>

## Setup
python 3.11 is required (there are some problem of compatibility with python 3.12)

### Modules needed (manual installation)
- chromadb
- easyocr
- langchain
- langchain-chroma
- langchain-text-splitters
- ollama
- openai
- pdf2image
- pypdf
- pytorch (this one need CUDA setup)
- rapidocr-onnxruntime
- sentence
- unstructured
- "unstructured[all-docs]"
- torch
- torchaudio
- torchvision
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
5. Install the requirements:
    ```
    pip install -r requirements.txt
    ```

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
5. Install the requirements:
    ```
    pip install -r requirements.txt
    ```

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