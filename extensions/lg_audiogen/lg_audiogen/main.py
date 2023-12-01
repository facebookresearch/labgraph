import click
import torch
import datetime
from audiocraft.models import AudioGen
from audiocraft.data.audio import audio_write
from lg_audiogen.calendar_reader import calendar_to_dictionary, get_events_between_dates

DEFAULT_AUDIOGEN_MODEL = 'facebook/audiogen-medium'
DEFAULT_AUDIO_DURATION = 5
DEFAULT_DATE = datetime.datetime.now().strftime('%Y-%m-%d')

@click.command()
@click.argument('description', nargs=-1, required=False)
@click.option('--duration', '-d', default=DEFAULT_AUDIO_DURATION, help='Duration of the generated audio.')
@click.option('--model', '-m', default=DEFAULT_AUDIOGEN_MODEL, help='Name of the Audiocraft AudioGen model to use.')
@click.option('--output', '-o', help='Name of the output file.')
@click.option('--batch', '-b', type=click.Path(), help='File name for batch audio description.')
@click.option('--activities', '-a', help='Comma separated string or .ics file containing activities.')
@click.option('--gpt', is_flag=True, help='Enable GPT model for activities.')
@click.option('--deterministic', is_flag=True, help='Enable deterministic generation.')
@click.option('--dates', '-dt', default=DEFAULT_DATE, help='Date in the format \'YYYY-MM-DD\' or as a range: \'YYYY-MM-DD,YYYY-MM-DD\'.')
def parse_arguments(description, duration, model, output, batch, activities, gpt, deterministic, dates):
    """
    Generates audio from description using Audiocraft's AudioGen.
    """
    if activities:
       handle_activities(activities, gpt, deterministic, dates)
    elif batch:
        try:
            with open(batch, mode='r', encoding='utf-8') as f:
                descriptions = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            print(f"File {batch} not found. Please check the file path and try again.")
    else:
        if not description:
            raise click.BadParameter("Description argument is required when not using --batch.")
        descriptions = [' '.join(description)]
    #run_audio_generation(descriptions, duration, model, output)

def check_dates_format(dates):
    dates = dates.split(',')
    if len(dates) > 2:
        raise click.BadParameter("Dates must be in the format \'YYYY-MM-DD\' or as a range: \'YYYY-MM-DD,YYYY-MM-DD\'.")
    for date in dates:
        try:
            datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise click.BadParameter("Dates must be in the format \'YYYY-MM-DD\' or as a range: \'YYYY-MM-DD,YYYY-MM-DD\'.")
    return dates

def handle_activities(activities, gpt, deterministic, dates):
    if activities.endswith('.ics'):
        dates = check_dates_format(dates)
        calendar_events = calendar_to_dictionary(activities)
        # -1 trick to get the last element of the list (end date or single date)
        sorted_events = get_events_between_dates(calendar_events, dates[0], dates[-1])
        print(sorted_events)
    else:
        activities = activities.split(',')
        print(activities)

def run_audio_generation(descriptions, duration, model_name, output):
    """
    Load Audiocraft's AudioGen model and generate audio from the description.

    @param descriptions: The parsed arguments.
    @param duration: Duration of the generated audio.
    @param model_name: Name of the Audiocraft AudioGen model to use.
    @param output: Name of the output file.
    """
    print(f"Running lg_audiogen with descriptions: {descriptions}")

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
        audio_write(f'{batch_output}{idx}', one_wav.cpu(),
                    model.sample_rate, strategy="loudness", loudness_compressor=True)
