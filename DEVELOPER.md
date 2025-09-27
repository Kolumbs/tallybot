# developer docs

Meant for developers who want to contribute to tallybot project.

## Dev environment

### install dependencies
```bash
python3.11 -m venv env
env/bin/pip install -r requirements.txt
env/bin/pip install -r requirements-dev.txt
# Make tallybot editable install
env/bin/pip install -e .
```


## Releases

install pre-push hook to run release deployment

```bash
cd .git/hooks/ && ln -s ../../tools/githooks/pre-push . && cd -
```

## Commits

install pre-commit hook to run tests before commiting code

```bash
cd .git/hooks/ && ln -s ../../tools/githooks/pre-commit . && cd -
```
