import os
import subprocess

def test_single_description():
    '''
        Tests output with a single description
    '''
    # Run the script with an example description
    subprocess.run(["lg_audiogen", "dog barking"],
                   capture_output=True, text=True, check=False)
    # Assert that the output file was created
    assert os.path.exists("dog_barking0.wav"), "Output file dog_barking0.wav was not created"
    os.remove("dog_barking0.wav")

def test_activity_to_sound():
    '''
        Tests output with a single activity
    '''
    # Run the script with an example activity
    subprocess.run(["lg_audiogen", "-a", "meeting with nathan"],
                   capture_output=True, text=True, check=False)
    # print the ls command output
    print(subprocess.run(["ls"], capture_output=True, text=True, check=False))
    # Assert that the output file was created
    assert os.path.exists("meeting_with_nathan0.wav"), "Output file meeting_with_nathan0.wav was not created"
    os.remove("meeting_with_nathan0.wav")
