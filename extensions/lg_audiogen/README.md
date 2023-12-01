# Audiogen

Audiogen is a Python command-line tool that uses models from Audiocraft's AudioGen to generate audio from specified descriptions. This tool can generate a single piece of audio based on a specific description, multiple pieces of audio based on a batch file containing multiple descriptions, or based on activities from a string or an `.ics` calendar file.

## Features

* Ability to specify duration of the generated audio.
* Ability to generate audio based on a batch file.
* Ability to specify the model to be used for the audio generation.
* Ability to set the output file name.
* Ability to generate audio based on daily activities from a comma-separated string or a `.ics` calendar file.
* Ability to integrate with GPT models to enhance activity descriptions.
* Ability to enable pseudo-deterministic activity prompts
* Ability to specify a date or a range of dates to get events from the `.ics` calendar file. 

## Setup

Audiocraft needs Python 3.8 or higher to run. If you have a suitable version of Python installed, you can install Audiogen with pip:

```shell
pip install -e .
```

## Usage

### Command-line interface

The CLI usage for Audiogen is `lg_audiogen [OPTIONS] [DESCRIPTION]...`.

### Options

* `description`: the description based on which the audio is to be generated.
* `duration, -d`: duration of the generated audio, default is 5.
* `model, -m`: name of the Audiocraft AudioGen model to use, default is 'facebook/audiogen-medium'.
* `output, -o`: name of the output file.
* `batch`: file name for batch audio description.
* `activities, -a`: comma-separated string or `.ics` calendar file containing events.
* `gpt`: New: flag to enable GPT model for activities description enhancement.
* `deterministic`: New: flag to enable deterministic generation.
* `dates, -dt`: New: date in the format 'YYYY-MM-DD' or as a range 'YYYY-MM-DD,YYYY-MM-DD'.

### Example

To generate an audio file you would use the following command:

```shell
lg_audiogen -d 5 -m 'facebook/audiogen-medium' -o 'my_output' 'dog barking'

lg_audiogen 'dog barking'

lg_audiogen -b 'batch.txt'

lg_audiogen -a 'meeting with nathan, lunch with friends' -gpt -deterministic

lg_audiogen -a "calendar.ics" -gpt -dt '2023-11-29,2023-12-01'
```

**Note:** for GPT usage, create a `.env` file with the same format as the `sample.env` file provided.

### Batch File Format

The batch file should contain one description per line. The descriptions should be in the same format as the descriptions used in the command-line interface.

Example:

*batch.txt*
```txt
Natural sounds of a rainforest
Bird Chirping in the background 
```

### Samples

[Google Drive Folder](https://drive.google.com/drive/folders/1kdWB1CBog4NGVJ7jWddKLtBAuPm3gwDq?usp=drive_link)

## O.S Support

```Tested on Ubuntu 22.04 (Jammy) LTS```

## Error Handling

If the batch file is not found, a notable error message will be presented. Moreover, if a description is not provided when not using a batch file, a misusage error will be raised.
