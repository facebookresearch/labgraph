from setuptools import setup, find_packages

setup(
    name='lg_audiogen',
    version='0.1',
    description="Audio generation on labgraph",
    packages=find_packages(),
    install_requires=[
        'Click',
        "torchaudio",
        "audiocraft",
    ],
    entry_points='''
        [console_scripts]
        lg_audiogen=lg_audiogen.main:parse_arguments
    ''',
)