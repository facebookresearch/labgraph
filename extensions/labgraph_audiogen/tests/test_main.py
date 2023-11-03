import os
import subprocess

def test_single_description():
    # Run the script with an example description
    process = subprocess.run(["labgraph_audiogen", "dog barking", "dog barking"], capture_output=True, text=True)
    
    # Assert that the output file was created
    assert os.path.exists("dog_barking0.wav"), "Output file dog_barking0.wav was not created"
    os.remove("dog_barking0.wav")