import click
import torch
from audiocraft.models import AudioGen
from audiocraft.data.audio import audio_write

DEFAULT_AUDIOGEN_MODEL = 'facebook/audiogen-medium'
DEFAULT_AUDIO_DURATION = 5

@click.command()
@click.argument('description', nargs=-1, required=False)
@click.option('--duration', '-d', default=DEFAULT_AUDIO_DURATION, help='Duration of the generated audio.')
@click.option('--model', '-m', default=DEFAULT_AUDIOGEN_MODEL, help='Name of the Audiocraft AudioGen model to use.')
@click.option('--output', '-o', help='Name of the output file.')
@click.option('--batch', type=click.Path(), help='File name for batch audio description.')
def parse_arguments(description, duration, model, output, batch):
    """
    Generates audio from description using Audiocraft's AudioGen.
    """
    if batch:
        try:
            with open(batch, 'r') as f:
                descriptions = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            print(f"File {batch} not found. Please check the file path and try again.")
    else:
        if not description:
            raise click.BadParameter("Description argument is required when not using --batch.")
        descriptions = [' '.join(description)]
    
    run_audio_generation(descriptions, duration, model, output)

def run_audio_generation(descriptions, duration, model_name, output):
    """
    Load Audiocraft's AudioGen model and generate audio from the description.

    :param descriptions: The parsed arguments.
    :param duration: Duration of the generated audio.
    :param model_name: Name of the Audiocraft AudioGen model to use.
    :param output: Name of the output file.
    """
    print(f"Running labgraph_audiogen with descriptions: {descriptions}")

    # Load Audiocraft's AudioGen model and set generation params.
    model = AudioGen.get_pretrained(model_name)
    model.set_generation_params(duration=duration)

    # Generate audio from the descriptions
    wav = model.generate(descriptions)
    batch_output = output
    # Save the generated audios.
    for idx, one_wav in enumerate(wav):
        # Will save under {output}{idx}.wav, with loudness normalization at -14 db LUFS.
        if not output:
            batch_output = descriptions[idx].replace(' ', '_')
        audio_write(f'{batch_output}{idx}', one_wav.cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)