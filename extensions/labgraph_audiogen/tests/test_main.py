import os
import subprocess

def test_main():
    # Run the script with an example description
    process = subprocess.run(["labgraph_audiogen", "--description", "dog barking"], capture_output=True, text=True)
    
    # Assert that the output file was created
    assert os.path.exists("0.wav"), "Output file 0.wav was not created"
    os.remove("0.wav")