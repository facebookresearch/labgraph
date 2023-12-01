from setuptools import setup, find_packages

setup(
    name='lg_audiogen',
    version='0.1',
    description="A Command-line interface to use Audiocraft for labgraph",
    long_description="""
    A Command-line interface to facilitate the usage of Audiocraft's models
    to generate and process audio on labgraph
    """,
    packages=find_packages(),
    install_requires=[
        "Click>=8.1.7",
        "torch>=2.1.0",
        "torchaudio>=2.1.0",
        "audiocraft==1.1.0",
        "icalendar==5.0.11",
        "openai==1.3.6"
    ],
    entry_points='''
        [console_scripts]
        lg_audiogen=lg_audiogen.main:parse_arguments
    ''',
)