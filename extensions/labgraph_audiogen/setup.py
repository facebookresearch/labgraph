from setuptools import setup


setup(
    name="labgraph_audiogen",
    version="0.0.1",
    description="A command-line interface for the usage of AudioCraft for labgraph",
    long_description="A command-line interface to facilitate the usage of the models of Audiocraft to generate and process audio on labgraph",
    packages=["labgraph_audiogen"],
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        labgraph_audiogen=labgraph_audiogen.main:main
    """
)