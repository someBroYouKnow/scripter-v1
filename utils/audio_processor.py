from pydub import AudioSegment
import os

def convert_m4a_to_mono(input_path: str, output_path: str):

    # check if the input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    # Load the M4A file
    audio = AudioSegment.from_file(input_path, format="m4a")

    # Convert to mono (single channel)
    mono_audio = audio.set_channels(1)

    # Export as needed - you can keep it as M4A or convert to WAV
    mono_audio.export(output_path, format="wav")
    # or export as WAV if your model needs that
    # mono_audio.export(output_path, format="wav")