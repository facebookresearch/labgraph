import click


# All models supported by the lg_audiogen command
SUPPORTED_MODELS = [
    "audiogen-medium",
    "musicgen-small",
    "musicgen-medium",
    "musicgen-melody",
    "musicgen-large"
]

# Musicgen models supported by the lg_audiogen command
MUSICGEN_MODELS = [
    "musicgen-small",
    "musicgen-medium",
    "musicgen-melody",
    "musicgen-large"
]


def generate_text_music(descriptions, duration, output, musicgen_model):
    """
    Generate music from the given descritptions and save it on the outputs folder

    @param descriptions: list of descriptions to generate music from
    @param duration: duration of the audio to generate
    @param output: name of the output file
    @param musicgen_model: name of the musicgen model to use
    """
    click.secho("\nStarting the music generation from the given descriptions", fg="bright_blue")

    # Import MusicGen, audio_write in this function to avoid time consuming imports
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write

    # Load the corresponding MusicGen model and set the generation parameters
    model = MusicGen.get_pretrained(f"facebook/{musicgen_model}")
    model.set_generation_params(duration=duration)

    filenames = []
    # Validate the descriptions and filenames
    for i, description in enumerate(descriptions):
        if not output:
            filenames.append(f"{description.replace(' ', '_')}")
        else:
            filenames.append(output.replace(' ', '_') + str(i))

        if len(description) == 0:
            raise click.BadParameter(
                click.style(
                    f"Description too short for {description}, "
                    "please use a non-empty description",
                    fg="bright_red"
                )
            )

        click.secho(
            f"Generating music from '{description}' written on the '{filenames[i]}.wav' file",
            fg="bright_green"
        )

    try:
        # Generate the music from the descriptions
        music = model.generate(descriptions, progress=True)
        # Save the music on the outputs folder with the corresponding filename
        for i, generation in enumerate(music):
            audio_write(f"outputs/{filenames[i]}", generation.cpu(), model.sample_rate,
                        strategy="loudness", loudness_compressor=True)

            click.secho(
                f"Audio generated and saved on the outputs/{filenames[i]}.wav file",
                bg="green", fg="black"
            )

    except Exception as music_error:
        click.secho(f"Error generating music: {music_error}", bg="red", fg="white")


@click.command()
@click.version_option()
@click.argument('description', nargs=-1, required=False)
@click.option("-d", "--duration", type=int, prompt_required=False, help="Duration of the audio")
@click.option("-m", "--model", type=click.Choice(SUPPORTED_MODELS), help="Name of the model to use")
@click.option("-o", "--output", prompt_required=False, help="Name of the output file")
@click.option('--batch', '-b', type=click.Path(), help='File name for batch audio description.')
def parse_arguments(description, duration, model, output, batch):
    """
    A command-line command to facilitate the usage of the models of Audiocraft
    """
    # Validate batch and description
    if batch:
        try:
            with open(batch, mode='r', encoding='utf-8') as f:
                descriptions = [line.strip() for line in f.readlines()]
        except FileNotFoundError as file_error:
            raise click.FileError(filename=batch, hint=click.style(file_error, fg="bright_red"))
    else:
        if not description:
            raise click.BadParameter(
                click.style(
                    "Description argument is required when not using --batch.",
                    fg="bright_red"
                )
            )
        descriptions = [' '.join(description)]

    # Validate model and duration
    if not model:
        raise click.BadParameter(
            click.style(
                "No model provided, select a supported model with -m / --model "
                f"(eg. -m musicgen-medium) between {', '.join(SUPPORTED_MODELS)}",
                fg="bright_red"
            )
        )
    if not duration:
        click.secho(
            "No duration provided, select a duration with -d / --duration, 10 seconds will be used",
            fg="yellow"
        )
        duration = 10
    if duration <= 0:
        raise click.BadParameter(
            click.style(
                "Duration must be greater than 0", fg="bright_red"
            )
        )

    if model in MUSICGEN_MODELS:
        generate_text_music(descriptions, duration, output, model)
