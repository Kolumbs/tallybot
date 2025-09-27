:autocmd BufWritePost *.py !env/bin/flake8 % && env/bin/mypy %
:command Format !env/bin/docformatter --in-place % && env/bin/black %
:command -nargs=? Test !env/bin/python -m unittest --failfast <args>
