:autocmd BufWritePost *.py !env/bin/flake8 %
:command Format !env/bin/docformatter --in-place % && env/bin/black % && env/bin/isort %
:command -nargs=? Test !env/bin/python -m unittest --failfast <args>
