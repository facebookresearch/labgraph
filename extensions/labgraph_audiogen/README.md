# LabGraph AudioGen Extension

A powerful Python command-line command for Windows. This tool facilitates the creation, processing, and autocompletion high-quality audio and music, using the AudioCraft models, AudioGen, and MusicGen.

The command is the `lg_audiogen` command, which can be installed with the `labgraph_audiogen` extension.

## Features

- Ability to specify duration of the generated audio.
- Ability to generate music based on a batch file.
- Ability to specify the model to be used for the audio generation.
- Ability to set the output file name.
- Ability to generate music within 4 different models.

## Setup

Audiocraft needs Python 3.8 or higher to run. If you have a suitable version of Python installed, you can install Audiogen with pip:

```bash
cd extensions/labgraph_audiogen  # Only if you are not already in this directory
pip install -e .
```

## Usage

```bash
lg_audiogen --help
```

Usage: lg_audiogen [OPTIONS] [DESCRIPTION]...

A command-line command to facilitate the usage of the models of Audiocraft

Options:

- `--version:` Show the version and exit.
- `-d, --duration:` INTEGER with the duration of the audio
- `-m, --model:` Name of the model to use between *[audiogen-medium | musicgen-small | musicgen-medium | musicgen-melody | musicgen-large]*
- `-o, --output:` TEXT with the name of the output file
- `-b, --batch:` PATH to file for batch audio description.
- `--help:` Show this message and exit.

## Examples

```bash
lg_audiogen -m musicgen-melody -d 15 -o "mariachi_rnb" "An rnb beat with some mariachi trumpets"

lg_audiogen -m musicgen-small "A happy mood in a rainy day"
```

Outputs:

- [mariachi_rnb.wav](https://drive.google.com/file/d/1OKXcZtRIqfL_dvfRFGtZV7VwC9CCUDX-/view)
- [A_happy_mood_in_a_rainy_day.wav](https://drive.google.com/file/d/1cCFhL7PP8FO0uzkEeRlhbDSGoflsBJ-G/view)
