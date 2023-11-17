from setuptools import setup


setup(
    name="lg_audiogen",
    version="0.0.1",
    description="A command-line command for the usage of AudioCraft for labgraph",
    long_description="""
    A command-line command to facilitate the usage of the models of Audiocraft 
    to generate and process audio on labgraph
    """,
    packages=["lg_audiogen"],
    install_requires=[
        "Click>=8.1.7",
        "torch>=2.1.0",
        "torchaudio>=2.1.0",
        "audiocraft>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'lg_audiogen=lg_audiogen.main:parse_arguments',
        ],
    },
)
