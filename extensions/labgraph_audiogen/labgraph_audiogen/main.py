import click
import torch
from audiocraft.models import AudioGen
from audiocraft.data.audio import audio_write

DEFAULT_AUDIOGEN_MODEL = 'facebook/audiogen-medium'
DEFAULT_AUDIO_DURATION = 5

@click.command()
@click.argument('description', nargs=-1, required=True)
@click.option('--duration', '-d', default=DEFAULT_AUDIO_DURATION, help='Duration of the generated audio.')
@click.option('--model', '-m', default=DEFAULT_AUDIOGEN_MODEL, help='Name of the Audiocraft AudioGen model to use.')
@click.option('--output', '-o', help='Name of the output file.')
def parse_arguments(description, duration, model, output):
    """
    Generates audio from description using Audiocraft's AudioGen.
    """
    description = ' '.join(description)
    if output is None:
        output = description[:10]

    run_audio_generation(description, duration, model, output)


def run_audio_generation(description, duration, model_name, output):
    """
    Load Audiocraft's AudioGen model and generate audio from the description.

    :param description: The parsed arguments.
    :param duration: Duration of the generated audio.
    :param model_name: Name of the Audiocraft AudioGen model to use.
    :param output: Name of the output file.
    """
    print(f"Running labgraph_audiogen with description: {description}")

    # Load Audiocraft's AudioGen model and set generation params.
    model = AudioGen.get_pretrained(model_name)
    model.set_generation_params(duration=duration)

    # Generate audio from the description
    wav = model.generate([description])

    # Save the generated audios.
    for idx, one_wav in enumerate(wav):
        # Will save under {output}{idx}.wav, with loudness normalization at -14 db LUFS.
        audio_write(f'{output}', one_wav.cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)