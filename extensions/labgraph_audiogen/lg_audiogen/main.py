import click


DEFAULT_AUDIOGEN_MODEL = 'facebook/audiogen-medium'
DEFAULT_MUSICGEN_MODEL = "facebook/musicgen-medium"
DEFAULT_AUDIO_DURATION = 10


def generate_text_music(description, duration, output, musicgen_model):
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
    model = MusicGen.get_pretrained(musicgen_model)
    model.set_generation_params(duration=duration)
    outputs = []
    for i, text in enumerate(description):
        if not output:
            output = text[:10] if len(text) >= 10 else text
        if len(text) > 100:
            raise click.BadParameter(click.style(f"Description too long for {text}, please use a description of lees than 100 characters", fg="bright_red"))
        if len(text) < 1:
            raise click.BadParameter(click.style(f"Description too short for {text}, please use a description of more than 1 character", fg="bright_red"))
        output = output.replace(" ", "_")
        click.secho(f"Generating music from '{text}' written on the '{output}{i}.wav' file\n", fg="bright_green")
        outputs.append(f"{output}{i}")
    music = model.generate(description, progress=True)
    for i, generation in enumerate(music):
        audio_write(f"outputs/{outputs[i]}", generation.cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)
        click.secho(f"Audio generated and saved on the 'outputs/{outputs[i]}.wav' file", bg="green", fg="black")


def generate_text_audio(text, duration, output):
    click.secho(f"\nGenerating audio from text '{text}' with a duration of {duration}s and written on the {output}.wav", fg="bright_green")
    return text


@click.command()
@click.argument('description', nargs=-1, required=False)
@click.option("-d", "--duration", prompt="Enter the duration of the audio", prompt_required=False, help="Duration of the audio to generate")
@click.option("-m", "--model", type=click.Choice(["audiogen", "musicgen"]), help="Select the model to run")
@click.option("-o", "--output", prompt="Enter the desired output file name", prompt_required=False, help="Name of the output file")
def main(description, duration, model, output):
    if not model:
        raise click.BadParameter(click.style("No model provided, set your model with the -m / --model flag (e.g. labgraph_audiogen -m audiogen)", fg="bright_red"))
    if not description:
        raise click.BadParameter(click.style("No text provided, set your text with the -t / --text flag (e.g. labgraph_audiogen -m audiogen -t 'Hello World')", fg="bright_red"))
    if not duration:
        click.secho("No duration provided, set you duration using -d / --duration, default will be used (10 seconds)", fg="yellow")
        duration = 10
    else:
        duration = int(duration)

    descriptions = [' '.join(description)]
    if model == "audiogen":
        audiogen_model = DEFAULT_AUDIOGEN_MODEL
        generate_text_audio(descriptions, duration, output, audiogen_model)
    elif model == "musicgen":
        musicgen_model = DEFAULT_MUSICGEN_MODEL
        generate_text_music(descriptions, duration, output, musicgen_model)