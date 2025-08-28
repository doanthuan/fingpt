# FinGPT

## I. How to setup for local run??

1. Clone this `fin-gpt` repo to your local.

2. Make sure your python enviroment has installed `poetry` and `python 3.11.4`.

3. From your terminal

   1. Run `cd /path/to/your/repo/fin-gpt/fingpt`.

   2. Run `poetry install` to set up all the necessary libraries.

   3. `./cmd.sh run` then see the deployment on `http://localhost:8000/docs`.


## II. Pre-commit set up
Use `pre-commit` to manage hooks for checking your code before commit to GitHub.

1. Set up pre-commit

```
    pip install pre-commit
```
```
    pre-commit install
```
2. Do commit as normal.

If your commit code not clean or contains any secret keys, it will fix it for you or stop you to re-check!
