import time
from sys import modules as mod
import os

import torch
from scipy.io.wavfile import write

from utils.tools import prepare_text

try:
    import winsound
    os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = r'C:\Program Files\eSpeak NG\libespeak-ng.dll'
    os.environ['PHONEMIZER_ESPEAK_PATH'] = r'C:\Program Files\eSpeak NG\espeak-ng.exe'
except ImportError:
    from subprocess import call

print("Initializing TTS Engine...")



# Select the device
if torch.is_vulkan_available():
    DEVICE = 'vulkan'
if torch.cuda.is_available():
    DEVICE = 'cuda'
else:
    DEVICE = 'cpu'

# Load models
glados = torch.jit.load('models/glados.pt')
vocoder = torch.jit.load('models/vocoder-gpu.pt', map_location=DEVICE)

# Prepare models in RAM
for i in range(4):
    init = glados.generate_jit(prepare_text(str(i)))
    init_mel = init['mel_post'].to(DEVICE)
    init_vo = vocoder(init_mel)

while True :
    text = input("Input: ")

    # Tokenize, clean and phonemize input text
    x = prepare_text(text).to('cpu')

    with torch.no_grad():

        # Generate generic TTS-output
        old_time = time.time()
        tts_output = glados.generate_jit(x)
        print("Forward Tacotron took " +
              str((time.time() - old_time) * 1000) + "ms")

        # Use HiFiGAN as vocoder to make output sound like GLaDOS
        old_time = time.time()
        mel = tts_output['mel_post'].to(DEVICE)
        audio = vocoder(mel)
        print("HiFiGAN took " + str((time.time() - old_time) * 1000) + "ms")

        # Normalize audio to fit in wav-file
        audio = audio.squeeze()
        audio = audio * 32768.0
        audio = audio.cpu().numpy().astype('int16')
        output_file = ('output.wav')

        # Write audio file to disk
        # 22,05 kHz sample rate
        write(output_file, 22050, audio)

        # Play audio file
        if 'winsound' in mod:
            winsound.PlaySound(output_file, winsound.SND_FILENAME)
        else:
            call(["aplay", "./output.wav"])
