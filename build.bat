@REM build setup.py on Windows as wheel

python setup.py bdist_wheel

python -m twine upload --repository pypi dist/*