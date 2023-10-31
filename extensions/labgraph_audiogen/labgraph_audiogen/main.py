import sys
import click


def generate_text_music(text, duration, output):
    click.echo(f"\nGenerating music from text '{text}' with a duration of {duration}s and written on the {output}.wav")
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
    model = MusicGen.get_pretrained("facebook/musicgen-medium")
    model.set_generation_params(
        use_sampling=True,
        top_k=250,
        duration=duration,
    )
    music = model.generate(text, progress=True)
    for generation in music:
        generation_cpu = generation.cpu()
        audio_write(f"outputs/{output}", generation_cpu, 32000)


def generate_text_audio(text, duration, output):
    click.echo(f"\nGenerating audio from text '{text}' with a duration of {duration}s and written on the {output}.wav")
    return text


@click.command(context_settings={"ignore_unknown_options": True})
@click.version_option()
@click.option("-m", "--model", type=click.Choice(["audiogen", "musicgen"]), help="Select the model to run")
@click.option("-t", "--text", prompt="Enter the text to generate audio from", prompt_required=False, help="Text to generate audio from")
@click.option("-d", "--duration", prompt="Enter the duration of the audio", prompt_required=False, help="Duration of the audio to generate")
@click.option("-o", "--output", prompt="Enter the desired output file name", prompt_required=False, help="Name of the output file")
def main(model, text, duration, output):
    if not model:
        click.echo("No model provided, set your model with the -m / --model flag (e.g. labgraph_audiogen -m audiogen)")
        return sys.exit(1)
    if not text:
        click.echo("No text provided, set your text with the -t / --text flag (e.g. labgraph_audiogen -m audiogen -t 'Hello World')")
        return sys.exit(1)
    if not duration:
        click.echo("No duration provided, set you duration using -d / --duration, default will be used (10 seconds)") 
        duration = 10
    else:
        duration = int(duration)
    if not output:
        click.echo("No output file name provided, set your output file name using -o / --output, default will be used (first 10 characters of the text)")
        output = text[:10] if len(text) >= 10 else text
    if len(output) > 35:
        click.echo("Output file name too long, please use a name with less than 35 characters")
        return sys.exit(1)
    if len(text) > 100:
        click.echo("Text too long, please use a text with less than 100 characters")
        return sys.exit(1)

    if model == "audiogen" and len(text) < 100:
        generate_text_audio(text, duration, output)
    elif model == "musicgen" and len(text) < 100:
        generate_text_music(text, duration, output)
