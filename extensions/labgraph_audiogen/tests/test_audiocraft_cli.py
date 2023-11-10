import os
import subprocess


def test_text_to_smallmusicgen():
    """
    Test the music generation from text with the musicgen-small model
    """
    # Run the lg_audiogen -m musicgen-small -d 3 -o test_audio.wav "A happy song"
    print(subprocess.run(["lg_audiogen", "-m", "musicgen-small", "-d", "3", "-o", "test_audio", "A happy song"],
                   capture_output=True, text=True))
    # Assert file exists and size
    print(subprocess.run(["ls", "-l"], capture_output=True, text=True))
    print(subprocess.run(["pwd"], capture_output=True, text=True))
    assert os.path.exists("outputs/test_audio0.wav"), "The file test_audio0.wav does not exist"
    assert os.path.getsize("outputs/test_audio0.wav") > 0, "The file test_audio0.wav is empty"
    # Remove the file
    os.remove("outputs/test_audio0.wav")
    os.rmdir("outputs")
