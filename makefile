SHELL = /usr/bin/env bash

# configure engine
python = python
pip = pip
# docs
pandocEngine = pdflatex
HTMLVersion = html5

test = $(wildcard tests/*.md)
testNative = $(patsubst %.md,%.native,$(test))
testAll = $(testNative)

# docs
CSSURL:=https://cdn.jsdelivr.net/gh/ickc/markdown-latex-css
pandocArgCommon = -f markdown+autolink_bare_uris-fancy_lists --toc -V linkcolorblue -V citecolor=blue -V urlcolor=blue -V toccolor=blue --pdf-engine=$(pandocEngine) -M date="`date "+%B %e, %Y"`"
## TeX/PDF
pandocArgFragment = $(pandocArgCommon) --filter=pantable
pandocArgStandalone = $(pandocArgFragment) --toc-depth=1 -s -N
## HTML/ePub
pandocArgHTML = $(pandocArgFragment) -t $(HTMLVersion) --toc-depth=2 -s -N -c $(CSSURL)/css/common.min.css -c $(CSSURL)/fonts/fonts.min.css
## GitHub README
pandocArgReadmeGitHub = $(pandocArgFragment) --toc-depth=2 -s -t markdown_github --reference-location=block
pandocArgReadmePypi = $(pandocArgFragment) -s -t rst --reference-location=block -f markdown+autolink_bare_uris-fancy_lists-implicit_header_references

docsAll = gh-pages/README.pdf gh-pages/index.html README.md README.rst README.html

# Main Targets #################################################################

.PHONY: all docs test testFull clean

all: $(testAll)

docs: $(docsAll)

test: pytest
	coverage html
testFull: pytest pep8 pylint
	coverage html

clean:
	rm -f .coverage $(testAll) tests/reference_idempotent.native $(docsAll)
	rm -rf htmlcov pantable.egg-info .cache .idea dist
	find . -type f \( -name "*.py[co]" -o -name ".coverage.*" \) -delete -or -type d -name "__pycache__" -delete
	find tests -name '*.pdf' -delete

# Making dependancies ##########################################################

%.native: %.md
	pandoc -t json $< | coverage run --append --branch -m pantable.cli.pantable | pandoc -f json -t native -o $@

# maintenance ##################################################################

.PHONY: pypi pypiManual pytest pytestLite pep8 pylint autopep8 autopep8Aggressive
# Deploy to PyPI
## by CI, properly git tagged
pypi:
	git tag -a v$$($(python) setup.py --version) -m 'Deploy to PyPI' && git push origin v$$($(python) setup.py --version)
## Manually
pypiManual:
	$(python) setup.py sdist bdist_wheel && twine upload dist/*

pytest: $(testNative) tests/test_idempotent.native
	$(python) -m pytest -vv --cov=pantable --cov-branch tests
pytestLite:
	$(python) -m pytest -vv --cov=pantable --cov-branch --cov-append tests
tests/reference_idempotent.native: tests/test_pantable.md
	pandoc -t json $< |\
		coverage run --append --branch -m pantable.cli.pantable | coverage run --append --branch -m pantable.cli.pantable2csv |\
		coverage run --append --branch -m pantable.cli.pantable | coverage run --append --branch -m pantable.cli.pantable2csv |\
		pandoc -f json -t native > $@
tests/test_idempotent.native: tests/reference_idempotent.native
	pandoc -f native -t json $< |\
		coverage run --append --branch -m pantable.cli.pantable | coverage run --append --branch -m pantable.cli.pantable2csv |\
		pandoc -f json -t native > $@

# check python styles
pep8:
	pycodestyle . --ignore=E402,E501,E731
pylint:
	pylint pantable

# cleanup python
autopep8:
	autopep8 . --recursive --in-place --pep8-passes 2000 --verbose
autopep8Aggressive:
	autopep8 . --recursive --in-place --pep8-passes 2000 --verbose --aggressive --autopep8Aggressive

print-%:
	$(info $* = $($*))

# gh-pages #####################################################################

gh-pages/%.pdf: docs/%.md
	pandoc $(pandocArgStandalone) -o $@ $<
gh-pages/%.html: docs/%.md
	pandoc $(pandocArgHTML) $< -o $@

# readme
## index.html
gh-pages/index.html: docs/badges.markdown docs/README.md
	pandoc $(pandocArgHTML) $^ -o $@
## GitHub README
README.md: docs/badges.markdown docs/README.md
	printf "%s\n\n" "<!--This README is auto-generated from \`docs/README.md\`. Do not edit this file directly.-->" > $@
	pandoc $(pandocArgReadmeGitHub) $^ >> $@
## PyPI README: not using this for now as rst2html emits errors
README.rst: docs/badges.markdown docs/README.md
	printf "%s\n\n" ".. This README is auto-generated from \`docs/README.md\`. Do not edit this file directly." > $@
	pandoc $(pandocArgReadmePypi) $^ >> $@
README.html: README.rst
	rst2html.py $< > $@
