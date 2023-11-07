import click


DEFAULT_AUDIOGEN_MODEL = 'facebook/audiogen-medium'
DEFAULT_MUSICGEN_MODEL = "facebook/musicgen-medium"
DEFAULT_AUDIO_DURATION = 10


def generate_text_music(text, duration, output, musicgen_model):
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
    click.echo(click.style(f"\nGenerating music from text '{text}' with a duration of {duration}s and written on the {output}.wav", fg="bright_green"))
    model = MusicGen.get_pretrained(musicgen_model)
    model.set_generation_params(duration=duration)
    music = model.generate(text, progress=True)
    for generation in music:
        audio_write(f"outputs/{output}", generation.cpu(), model.sample_rate)


def generate_text_audio(text, duration, output):
    click.echo(click.style(f"\nGenerating audio from text '{text}' with a duration of {duration}s and written on the {output}.wav", fg="bright_green"))
    return text


@click.command()
@click.version_option()
@click.option("-m", "--model", type=click.Choice(["audiogen", "musicgen"]), help="Select the model to run")
@click.option("-t", "--text", prompt="Enter the text to generate audio from", prompt_required=False, help="Text to generate audio from")
@click.option("-d", "--duration", prompt="Enter the duration of the audio", prompt_required=False, help="Duration of the audio to generate")
@click.option("-o", "--output", prompt="Enter the desired output file name", prompt_required=False, help="Name of the output file")
def main(model, text, duration, output):
    if not model:
        raise click.BadParameter(click.style("No model provided, set your model with the -m / --model flag (e.g. labgraph_audiogen -m audiogen)", fg="bright_red"))
    if not text:
        raise click.BadParameter(click.style("No text provided, set your text with the -t / --text flag (e.g. labgraph_audiogen -m audiogen -t 'Hello World')", fg="bright_red"))
    if not duration:
        click.echo(click.style("No duration provided, set you duration using -d / --duration, default will be used (10 seconds)", fg="yellow"))
        duration = 10
    else:
        duration = int(duration)
    if not output:
        click.echo(click.style("No output file name provided, set your output file name using -o / --output, default will be used (first 10 characters of the text)", fg="yellow"))
        output = text[:10] if len(text) >= 10 else text
    if len(output) > 35:
        raise click.BadParameter(click.style("Output file name too long, please use a name with less than 35 characters", fg="bright_red"))
    if len(text) > 100:
        raise click.BadParameter(click.style("Text too long, please use a text with less than 100 characters", fg="bright_red"))

    if model == "audiogen":
        audiogen_model = DEFAULT_AUDIOGEN_MODEL
        generate_text_audio(text, duration, output, audiogen_model)
    elif model == "musicgen":
        musicgen_model = DEFAULT_MUSICGEN_MODEL
        generate_text_music(text, duration, output, musicgen_model)
