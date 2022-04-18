# Use Flake8 for styling checks

**Install Flake8**:
https://flake8.pycqa.org/en/latest/

```bash
python -m pip install flake8
```

**Use Flake8 to check your code before submission**:

```bash
flake8 --config .flake8 [file_name]
```

# Use pre-commit hooks for code consistency

**Install pre-commit**:
https://pre-commit.com/

```bash
pip install pre-commit
```

**Install the git hooks script**:

```bash
pre-commit install
```

It uses a file called `.pre-commit-config.yaml` to create a Git hook `.git/hooks/pre-commit`

**Commit your changes**:

```bash
git commit -m "Your Message"
```

and it will automatically run `black` and `flake8` on the files you changed

```bash
git commit -m "Added pre-commit hook documentation"
black................................................(no files to check)Skipped
Flake8...............................................(no files to check)Skipped
[pre-commit-hooks 1d3d92f] Added pre-commit hook documentation
 1 file changed, 27 insertions(+), 2 deletions(-)
 ```