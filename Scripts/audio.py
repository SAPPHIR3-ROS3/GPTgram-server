from warnings import filterwarnings

filterwarnings("ignore", category=DeprecationWarning)
filterwarnings("ignore", category=FutureWarning)
filterwarnings("ignore", category=UserWarning)

from os import makedirs
from Scripts.utils import formatMessage
from Scripts.utils import DEBUG_LOG_LEVEL
from Scripts.utils import ERROR_LOG_LEVEL
from Scripts.utils import INFO_LOG_LEVEL
from Scripts.utils import log
import torch
from transformers import AutoModelForSpeechSeq2Seq
from transformers import AutoProcessor
from transformers import pipeline

currentLogLevel = INFO_LOG_LEVEL
SRMODEL = "openai/whisper-large-v3" # openai/whisper-large-v3

def transcribe(audioPath):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        SRMODEL, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained(SRMODEL)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=444,
        return_timestamps=True,
        torch_dtype=torch_dtype,
        device=device,
    )

    transcript = pipe(audioPath)

    return transcript['text']

def transcribeUserAudio(user: str, chatId: str, audioStr):
    if audioStr.endswith('.mp3'):
        audioStr += '.mp3'

    audioPath = f'./{user}/chats/{chatId}/audios/{audioStr}'
    transcript = transcribe(audioPath)

    return transcript

def convertAudioBlobToFile(blob: bytes, user: str, chatId: str, audioStr):
    audioPath = f'./users-data/{user}/chats/{chatId}/audios/'
    #makedirs(audioPath, exist_ok=True)

    audioPath += f'{audioStr}.mp3'

    with open(audioPath, 'wb') as f:
        f.write(blob)

    log(currentLogLevel, INFO_LOG_LEVEL, 'audio saved to', {'path ': audioPath})

    return audioPath

if __name__ == "__main__":
    trancription = transcribe