#!/usr/bin/env python3

r"""
Panflute filter to parse table in fenced YAML code blocks.
Currently only CSV table is supported.

7 metadata keys are recognized:

-   caption: the caption of the table. If omitted, no caption will be inserted.
-   alignment: a string of characters among L,R,C,D, case-insensitive,
        corresponds to Left-aligned, Right-aligned,
        Center-aligned, Default-aligned respectively.
    e.g. LCRD for a table with 4 columns
    default: DDD...
-   width: a list of relative width corresponding to the width of each columns.
    default: auto calculate from the length of each line in table cells.
-   table-width: the relative width of the table (e.g. relative to \linewidth).
    default: 1.0
-   header: If it has a header row. default: true
-   markdown: If CSV table cell contains markdown syntax. default: False
-   include: the path to an CSV file.
    If non-empty, override the CSV in the CodeBlock.
    default: None

When the metadata keys is invalid, the default will be used instead.

e.g.

```table
---
caption: '*Awesome* **Markdown** Table'
alignment: RC
table-width: 0.7
markdown: True
---
First row,defaulted to be header row,can be disabled
1,cell can contain **markdown**,"It can be aribrary block element:

- following standard markdown syntax
- like this"
2,"Any markdown syntax, e.g.",$$E = mc^2$$
```
"""

import csv
import io
import os
import panflute


# begin helper functions
def to_bool(to_be_bool):
    """
    Do nothing if to_be_bool is boolean,
    return `False` if it is "false" or "no" (case-insensitive),
    otherwise return `True`.
    """
    if not isinstance(to_be_bool, bool):
        if str(to_be_bool).lower() in ("false", "no"):
            to_be_bool = False
        elif str(to_be_bool).lower() in ("true", "yes"):
            to_be_bool = True
        else:
            to_be_bool = True
            panflute.debug("""pantable: invalid boolean. \
Should be true/false/yes/no, case-insensitive.""")
    return to_be_bool
# end helper functions


def init_table_options(options):
    """
    Initialize the `options` output from `panflute.yaml_filter`.
    """
    caption = options.get('caption', None)
    alignment = options.get('alignment', None)
    width = options.get('width', None)
    table_width = options.get('table-width', 1.0)
    header = options.get('header', True)
    markdown = options.get('markdown', False)
    include = options.get('include', None)
    return (caption, alignment, width, table_width, header, markdown, include)


def check_table_options(caption, alignment, width, table_width, header, markdown, include):
    """
    Set the values in options to default if they are invalid:

    -   `width` set to `None` when invalid,
        each element in `width` set to `0` when negative
    -   `table-width` set to `1.0` if invalid or not positive
    -   `header` set to `True` if invalid
    -   `markdown` set to `True` if invalid
    """
    try:
        if width is not None:
            width = [(float(x) if x >= 0 else None)
                                for x in width]
            if None in width:
                width = None
                panflute.debug("pantable: invalid width")
    except (ValueError, TypeError):
        width = None
        panflute.debug("pantable: invalid width")
    try:
        if table_width <= 0:
            table_width = 1.0
            panflute.debug("pantable: invalid table-width")
    except (ValueError, TypeError):
        table_width = 1.0
        panflute.debug("pantable: invalid table-width")
    header = to_bool(header)
    markdown = to_bool(markdown)
    if include is not None:
        if not os.path.isfile(str(include)):
            include = None
            panflute.debug("pantable: include path is invalid")
    return (caption, alignment, width, table_width, header, markdown, include)


def parse_table_options(caption, alignment, width, table_width, header, markdown, include, raw_table_list):
    """
    `caption` is assumed to contain markdown,
        as in standard pandoc YAML metadata.
    `alignment` string is parsed into pandoc format (AlignDefault, etc.)
    `width` is auto-calculated if not given in YAML
    It also returns True when table has 0 total width.
    """
    # parse caption
    if caption is not None:
        caption = panflute.convert_text(
            str(caption)
        )[0].content
    # preparation: get no of columns of the table
    number_of_columns = len(raw_table_list[0])
    # parse alignment
    if alignment is not None:
        alignment = str(alignment)
        # truncate and debug if too long
        if len(alignment) > number_of_columns:
            alignment = alignment[0:number_of_columns]
            panflute.debug("pantable: alignment string is too long")
        # parsing
        parsed_alignment = [("AlignLeft" if each_alignment.lower() == "l"
                             else "AlignCenter" if each_alignment.lower() == "c"
                             else "AlignRight" if each_alignment.lower() == "r"
                             else "AlignDefault" if each_alignment.lower() == "d"
                             else None) for each_alignment in alignment]
        # debug if invalid; set to default
        if None in parsed_alignment:
            parsed_alignment = [(each_alignment if each_alignment is not None else "AlignDefault")
                                for each_alignment in parsed_alignment]
            panflute.debug("pantable: alignment string is invalid")
        # fill up with default if too short
        if number_of_columns > len(parsed_alignment):
            parsed_alignment += ["AlignDefault" for __ in range(
                number_of_columns - len(parsed_alignment))]
        alignment = parsed_alignment
    # calculate width
    isempty = False
    if width is None:
        width_abs = [max(
            [max(
                [len(line) for line in row[i].split("\n")]
            ) for row in raw_table_list]
        ) for i in range(number_of_columns)]
        width_tot = sum(width_abs)
        try:
            width = [
                width_abs[i] / width_tot * table_width
                for i in range(number_of_columns)
            ]
        except ZeroDivisionError:
            panflute.debug("pantable: table has zero total width")
            isempty = True
    return (caption, alignment, width, table_width, header, markdown, include, isempty)


def read_data(include, data):
    """
    read csv and return the table in list
    """
    if include is not None:
        with open(include) as file:
            raw_table_list = list(csv.reader(file))
    else:
        with io.StringIO(data) as file:
            raw_table_list = list(csv.reader(file))
    return raw_table_list


def regularize_table_list(raw_table_list):
    """
    When the length of rows are uneven, make it as long as the longest row.
    """
    max_number_of_columns = max(
        [len(row) for row in raw_table_list]
    )
    for row in raw_table_list:
        missing_number_of_columns = max_number_of_columns - len(row)
        if missing_number_of_columns > 0:
            row += ['' for __ in range(missing_number_of_columns)]
    return


def parse_table_list(markdown, raw_table_list):
    """
    read table in list and return panflute table format
    """
    table_body = []
    for row in raw_table_list:
        if markdown:
            cells = [
                panflute.TableCell(*panflute.convert_text(x))
                for x in row
            ]
        else:
            cells = [
                panflute.TableCell(panflute.Plain(panflute.Str(x)))
                for x in row
            ]
        table_body.append(panflute.TableRow(*cells))
    return table_body


def convert2table(options, data, **__):
    """
    provided to panflute.yaml_filter to parse its content as pandoc table.
    """
    # initialize table options from YAML metadata
    caption, alignment, width, table_width, header, markdown, include = init_table_options(options)
    # check table options: reset to default if invalid
    caption, alignment, width, table_width, header, markdown, include = check_table_options(caption, alignment, width, table_width, header, markdown, include)
    # parse csv data to list
    raw_table_list = read_data(include, data)
    # check empty table
    if not raw_table_list:
        panflute.debug("pantable: table is empty")
        return []
    # regularize table: all rows should have same length
    regularize_table_list(raw_table_list)
    # parse list to panflute table
    table_body = parse_table_list(markdown, raw_table_list)
    # parse table options
    caption, alignment, width, table_width, header, markdown, include, isempty = parse_table_options(caption, alignment, width, table_width, header, markdown, include, raw_table_list)
    # check empty table
    if isempty:
        panflute.debug("pantable: table is empty")
        return []
    # extract header row
    header_row = table_body.pop(0) if (
        len(table_body) > 1 and header
    ) else None
    return panflute.Table(
        *table_body,
        caption=caption,
        alignment=alignment,
        width=width,
        header=header_row
    )


def main(_=None):
    """
    Fenced code block with class table will be parsed using
    panflute.yaml_filter with the fuction convert2table above.
    """
    return panflute.run_filter(
        panflute.yaml_filter,
        tag='table',
        function=convert2table,
        strict_yaml=True
    )

if __name__ == '__main__':
    main()
