from setuptools import setup

setup(
    name='labgraph_audiogen',
    version='0.1',
    description="Audio generation on labgraph",
    packages=['labgraph_audiogen'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        labgraph_audiogen=labgraph_audiogen.main:main
    ''',
)