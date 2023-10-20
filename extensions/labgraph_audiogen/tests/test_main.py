def test_main():
    import subprocess
    process = subprocess.run(["labgraph_audiogen", "arg1", "arg2"], 
                             capture_output=True, text=True)
    assert process.stdout.strip() == "Hello World from labgraph_audiogen with args: arg1 arg2"