# GPTgram-server
## Setup
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

## IncompatibilityNote
this cause installation problem
```console
pip install "unstructured[image]"
pip install "unstructured[pdf]"
```
