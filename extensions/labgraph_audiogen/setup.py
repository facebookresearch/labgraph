from setuptools import setup, find_packages

setup(
    name='labgraph_audiogen',
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
        labgraph_audiogen=labgraph_audiogen.main:main
    ''',
)