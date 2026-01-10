import nemo.collections.asr as nemo_asr
from utils.audio_processor import convert_m4a_to_mono

## convert any required audio files if necessary
convert_m4a_to_mono('assets/audio/Recording.m4a', 'assets/audio/Recording.wav')

print(f"Initialising speech to text model...")

asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v3")

# output = asr_model.transcribe(['assets/audio/sample-audio.wav'])
output = asr_model.transcribe(['assets/audio/Recording.wav'])


print(output[0].text)
