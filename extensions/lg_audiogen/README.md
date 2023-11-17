# Audiogen

Audiogen is a Python command-line tool that uses models from Audiocraft's AudioGen to generate audio from specified descriptions. This tool can generate a single piece of audio based on a specific description or multiple pieces of audio based on a batch file containing multiple descriptions.

## Features

* Ability to specify duration of the generated audio.
* Ability to generate audio based on a batch file.
* Ability to specify the model to be used for the audio generation.
* Ability to set the output file name.

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

### Example

To generate an audio file you would use the following command:

```shell
lg_audiogen -d 5 -m 'facebook/audiogen-medium' -o 'my_output' 'dog barking'

lg_audiogen 'dog barking'

lg_audiogen -b 'batch.txt'
```

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
