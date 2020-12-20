# Revision history for Pantable

- v0.13.2: packaging change only: specified required versions for all dependencies including extras
- v0.13.1: util.py: fix `iter_convert_texts_markdown_to_panflute`
- v0.13:added pandoc 2.11.0.4+ & panflute 2+ support
    - pandoc 2.10 introduces a new table AST. This version provides complete support of all features supported in the pandoc AST. Hence, older pandoc versions are no longer supported. Install `pantable=0.12.4` if you need to use `pandoc<2.10`.
    - deprecated `pipe_tables`, `grid_tables`, `raw_markdown` options in pantable, which were introduced in v0.12. pantable v0.13 has a much better way to process markdown cells that these are no longer needed.
    - slight changes on markdown output which should be functionally identical. Both changes in pandoc and pantable cause this. See commit eadc6fb.
    - add `short-caption`, `alignment-cells`, `fancy_table`, `format`, `ms`, `ns_head`. See docs for details.
- v0.12.4: Require panflute<2 explicitly
    - panflute 2 is released to support pandoc API 1.22. This release ensures that version control is correct when people specify pantable==0.12 in the future.
- v0.12.3: Fixes test and CI; update on supported Python versions
    - migrate from Travis CI to GitHub Actions
    - supported Python versions are now 3.5-3.8, pypy3
    - minor update in README
- v0.12.2: Add `grid_tables`
- v0.12.1: add `include-encoding`, `csv-kwargs`
    - closes #36, #38. See doc for details on this new keys.
- v0.12: Drop Python 2 support; enhance CSV with markdown performance
    - Dropping Python2 support, existing Python 2 users should be fine with pip>=9.0. See <https://python3statement.org/practicalities/>.

    - add `pipe_tables`, `raw_markdown` options. See README for details. This for example will speed up CSV with markdown cells a lot (trading correctness for speed though.)