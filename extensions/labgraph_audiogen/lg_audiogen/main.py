import click


SUPPORTED_MODELS = ["audiogen-medium", "musicgen-small", "musicgen-medium", "musicgen-melody", "musicgen-large"]
DEFAULT_AUDIOGEN_MODEL = 'facebook/audiogen-medium'
DEFAULT_MUSICGEN_MODEL = "facebook/musicgen-medium"
DEFAULT_AUDIO_DURATION = 10


def generate_text_music(descriptions, duration, output, musicgen_model):
    """
    Generate music from the given descritptions
    
    @param descriptions: list of descriptions to generate music from
    @param duration: duration of the audio to generate
    @param output: name of the output file
    @param musicgen_model: name of the musicgen model to use
    """
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
    model = MusicGen.get_pretrained(musicgen_model)
    model.set_generation_params(duration=duration)
    outputs = []
    for i, description in enumerate(descriptions):
        if not output:
            output = description[:10] if len(description) >= 10 else description
        if len(description) > 100:
            raise click.BadParameter(click.style(f"Description too long for {description}, please use a description of lees than 100 characters", fg="bright_red"))
        if len(description) < 1:
            raise click.BadParameter(click.style(f"Description too short for {description}, please use a description of more than 1 character", fg="bright_red"))
        output = output.replace(" ", "_")
        click.secho(f"Generating music from '{description}' written on the '{output}{i}.wav' file\n", fg="bright_green")
        outputs.append(f"{output}{i}")
    music = model.generate(descriptions, progress=True)
    for i, generation in enumerate(music):
        audio_write(f"outputs/{outputs[i]}", generation.cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)
        click.secho(f"Audio generated and saved on the 'outputs/{outputs[i]}.wav' file", bg="green", fg="black")


def generate_text_audio(descriptions, duration, output, audiogen_model):
    """
    Generate audio from the given descritptions

    @param descriptions: list of descriptions to generate audio from
    @param duration: duration of the audio to generate
    @param output: name of the output file
    @param audiogen_model: name of the audiogen model to use
    """
    click.secho(f"\nGenerating audio from text '{descriptions}' with a duration of {duration}s and written on the {output}.wav", fg="bright_green")
    return descriptions


@click.command()
@click.argument('description', nargs=-1, required=False)
@click.option("-d", "--duration", prompt="Enter the duration of the audio", prompt_required=False, help="Duration of the audio to generate")
@click.option("-m", "--model", type=click.Choice(SUPPORTED_MODELS), help="Name of the model to use")
@click.option("-o", "--output", prompt="Enter the desired output file name", prompt_required=False, help="Name of the output file")
@click.option('--batch', '-b', type=click.Path(), help='File name for batch audio description.')
def main(description, duration, model, output, batch):
    """
    A command-line interface to manage the usage of the AudioCraft models
    """
    if batch:
        try:
            with open(batch, mode='r', encoding='utf-8') as f:
                descriptions = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            raise click.BadParameter(click.style(f"File {batch} not found. Please check the file path and try again.", fg="bright_red"))
    else:
        if not description:
            raise click.BadParameter(click.style("Description argument is required when not using --batch.", fg="bright_red"))
    if not model:
        raise click.BadParameter(click.style("No model provided, set your model with the -m / --model flag (eg. lg_audiogen -m audiogen-medium)", fg="bright_red"))
    else:
        model = "facebook/" + model
    if not duration:
        click.secho("No duration provided, set you duration using -d / --duration, default will be used (10 seconds)", fg="yellow")
        duration = 10
    else:
        duration = int(duration)

    descriptions = [' '.join(description)]
    if model == "facebook/audiogen-medium":
        generate_text_audio(descriptions, duration, output, model)
    else:
        generate_text_music(descriptions, duration, output, model)