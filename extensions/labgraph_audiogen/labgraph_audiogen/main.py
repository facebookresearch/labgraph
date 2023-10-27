import sys
import argparse
import torchaudio
from audiocraft.models import AudioGen
from audiocraft.data.audio import audio_write

def main(args=None):
    # Parse arguments
    parser = argparse.ArgumentParser(description='Generate audio from descriptions using Audiocraft\'s AudioGen.')
    parser.add_argument('--description', nargs='+', type=str, help='Description of the generated audio.')
    parser.add_argument('--duration', type=int, default=5, help='Duration of the generated audio.')
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    print(f"Running labgraph_audiogen with description: {args.description}")

    # Load Audiocraft's AudioGen model and set generation params.
    model = AudioGen.get_pretrained('facebook/audiogen-medium')
    model.set_generation_params(duration=args.duration)

    # Generate audio from the description
    wav = model.generate(args.description)

    # Save the generated audios.
    for idx, one_wav in enumerate(wav):
        # Will save under {idx}.wav, with loudness normalization at -14 db LUFS.
        audio_write(f'{idx}', one_wav.cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)

if __name__ == "__main__":
    main()