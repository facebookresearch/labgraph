# Sphinx Documentation for LabGraph

Sphinx is a tool that makes it easy to create intelligent and beautiful documentation, written by Georg Brandl and licensed under the BSD license. You can learn more about Sphinx at [sphinx-doc.org](https://www.sphinx-doc.org/en/master/)

## How to Update Documentation

1. Go to `~/labgraph/sphinx`

2. Install neccessary libraries
 - `pip install -U sphinx` according to Sphinx's [installation](https://www.sphinx-doc.org/en/master/usage/installation.html)
 - `pip install --upgrade myst-parser` for Sphinx's [markdown support](https://www.sphinx-doc.org/en/master/usage/markdown.html)

3. Create a Symbolic Link to the `~/labgraph/docs` directory if not present
 - `>labgraph/sphinx ln -s ../docs/ docs`
 - This is used to avoid moving the `docs` directory to the `sphinx` directory as it requires that all files be children of `sphinx`
 - You can learn more about the issue on [StackOverflow](https://stackoverflow.com/questions/10199233/can-sphinx-link-to-documents-that-are-not-located-in-directories-below-the-root)

4. Update `sphinx/index.rst` as you fit

5. Run `sphinx-build . _build` to render the files into HTML and check the result under `~/labgraph/sphinx/_build/html/index.html`

