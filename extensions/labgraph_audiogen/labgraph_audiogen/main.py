import click


def generate_text_music(text):
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
    print(f"Generating music from text '{text}'")
    model = MusicGen.get_pretrained("facebook/musicgen-small")
    model.set_generation_params(
        use_sampling=True,
        top_k=250,
        duration=8
    )
    music = model.generate(text, progress=True)
    for output in music:
        output_cpu = output.cpu()
        file_name = f"output/1.wav"
        audio_write(file_name, output_cpu, 32000)


def generate_text_audio(text):
    print(f"Generating audio from text '{text}'")
    return text


@click.command(context_settings={"ignore_unknown_options": True})
@click.version_option()
@click.option("-m", "--model", type=click.Choice(["audiogen", "musicgen"]), help="Select the model to run")#, required=True)
@click.option("-t", "--text", prompt="Enter the text to generate audio from", prompt_required=False, help="Text to generate audio from")
@click.option("-d", "--duration", prompt="Enter the duration of the audio", prompt_required=False, help="Duration of the audio to generate")
@click.option("-o", "--output", prompt="Enter the desired output file name", prompt_required=False, help="Name of the output file")
def main(model, text, duration, output):
    print("Hello World from labgraph_audiogen!")
    if not model:
        print("No model provided, set your model with the -m or --model flag (e.g. labgraph_audiogen -m audiogen)")
        return
    if not text:
        print("No text provided, set your text with the -t or --text flag (e.g. labgraph_audiogen -m audiogen -t 'Hello World')")
        return
    if model == "audiogen" and len(text) < 100:
        generate_text_audio(text)
    elif model == "musicgen" and len(text) < 100:
        generate_text_music(text)
    else:
        print(f"Model {model} not found")