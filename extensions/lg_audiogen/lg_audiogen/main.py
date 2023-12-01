import click
import torch
import datetime
from audiocraft.models import AudioGen
from audiocraft.data.audio import audio_write
from lg_audiogen.calendar_reader import calendar_to_dictionary, get_events_between_dates
from lg_audiogen.gpt_utility import query_gpt
from lg_audiogen.keyword_generator import get_prompts

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
       descriptions, output = handle_activities(activities, gpt, deterministic, dates)
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
    run_audio_generation(descriptions, duration, model, output)

def check_dates_format(dates):
    """
    Checks if the dates are in the correct format.
    
    @param dates: The dates to be checked. If a string is provided, it will be split by commas.
    
    @return: A list of dates.
    """
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
    """
    Handles the activities based on the given parameters.

    @param activities: The activities to be handled. If a string is provided, it will be split by commas.
    @param gpt: Flag indicating whether to use GPT for generating response.
    @param deterministic: Flag indicating whether to use deterministic mode for GPT response generation.
    @param dates: The dates to filter the activities. If a string is provided, it should be in the format 'YYYY-MM-DD'.

    @return: A tuple containing the response generated and the list of activities.
    """
    if activities.endswith('.ics'):
        dates = check_dates_format(dates)
        calendar_events = calendar_to_dictionary(activities)
        # -1 trick to get the last element of the list (end date or single date)
        sorted_events = get_events_between_dates(calendar_events, dates[0], dates[-1])
        # build a list of event name strings if event has a name
        activities = []
        for each_date in sorted_events:
            for each_event in sorted_events[each_date]:
                if each_event['name']:
                    activities.append(each_event['name'])
    else:
        activities = activities.split(',')
    if gpt:
        response = query_gpt(activities, deterministic)
    else:
        response = get_prompts(activities, deterministic)
    return response, activities

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
    batch_output = output if type(output) == str else ''
    # Save the generated audios.
    for idx, one_wav in enumerate(wav):
        # Will save under {output}{idx}.wav, with loudness normalization at -14 db LUFS.
        if not output:
            batch_output = descriptions[idx].replace(' ', '_')
        if type(output) == list and len(output) == len(descriptions):
            batch_output = output[idx]
        audio_write(f'{batch_output}{idx}', one_wav.cpu(),
                    model.sample_rate, strategy="loudness", loudness_compressor=True)
