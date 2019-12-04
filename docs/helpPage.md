## Theming

Default theme:

![default-theme][1]

Blue theme:
```python
from pyparam import params
params._theme = 'blue'
# same as examples/basic.py
```

![default-theme][13]

Plain theme:
```python
from pyparam import params
params._theme = 'plain'
# same as examples/basic.py
```

![theme_blue][14]

Customize theme based on default theme:
```python
dict(
    error   = colorama.Fore.RED,
    warning = colorama.Fore.YELLOW,
    title   = colorama.Style.BRIGHT + colorama.Fore.CYAN,  # section title
    prog    = colorama.Style.BRIGHT + colorama.Fore.GREEN, # program name
    default = colorama.Fore.MAGENTA,              # default values
    optname = colorama.Style.BRIGHT + colorama.Fore.GREEN,
    opttype = colorama.Fore.BLUE,
    optdesc = ''),
```
```python
import colorama
from pyparam import params
params._theme = dict(title = colorama.Style.BRIGHT + colorama.Fore.YELLOW)
# same as examples/basic.py
```

![theme_custom][15]

## Help options
By default, we use `-h`, `--help` and `-H` for users to explictly call the help page and exit. You may define you own by `params._htops = 'hlp'`

## Manipulation of help page
The data of the help page is managed by class `pyparam.help.Helps`. The whole help page is composed of sections, with a title and two types of contents `HelpItems` (plain content without options) and `HelpOptions` (content with options). You can add, delete, modify and query the sections and contents with the API provided by `pyparam`.
All you need to do is to pass a function to `params._helpx` to manipulate the help page.

- Full example
    `examples/helpPage.py`
    ```python
    from pyparam import params
    from pyparam.help import HelpOptions, HelpItems

    def helpx(helps):
        # # initiate it with an option
        # # or initiate with empty
        # helps.add('Java options', HelpOptions())
        # # or
        # helps.add('Java options', sectype = 'option')
        helps.add('Java options', ('-Xmx', '<SIZE>', 'set maximum Java heap size'))

        # add another option
        helps.select('Java options').add(
            ('-Xms', '<SIZE>', 'set initial Java heap size'))

        # add a section before USAGE
        # # or initiate with empty
        # helps.before('USAGE', 'Description', sectype = 'item')
        # # or
        # helps.before('USAGE', 'Description', HelpItems())
        helps.before('USAGE', 'Description', 'This is an example of help manipulation.')

        # add another line to description
        helps.select('Description').add('Another description')

        # add a line before 'Another description'
        helps.select('Description').before('Another description', 'One description')

        # add required option section before optional
        # because no required options defined
        helps.before('Optional options', 'Required Options', sectype = 'option')

        # add an option
        helps.select('Required options').add(
            ('-v',  # option name
                '',    # type
                # description in multiple lines
                'The verbosity\nSome very very long description\nabout this option.'
            ))

        # add a line to the description after 'The verbosity'
        helps.select('Required options') \
                .select('-v')[2] \
                .after('The verbosity', 'Default: 0')

        # add another
        helps.select('Required options').add(
            ('-d, --depend', '<DICT>', 'The dependencies.'))

        # add an option after -v
        helps.select('Required options').after('-v',
            ('--version', '[BOOL]', 'Show the version.'))

    params._helpx = helpx
    print(params._parse())
    ```

    ![helpx][16]

- Section, non-option item and item description selector

    You can select a selctor or non-option item using handy selector here. A selector can be:

    1. A regular expression compiled by `re.compile`
    2. A `perl` like regular expression, starting and ending with `/`
    3. A substring of the item

    !!! Note

        It's case-insensitive for 2 and 3. You may compile a regex by yourself with `re.compile(..., re.I)` to get a case-insenstive selector.
        The first item that matched will be returned.

- Option selector

    It's a little bit different for option selectors. It only search again the option names.
    - If a selector is of type 1 and 2 abovementioned, then the whole option name is to be searched. For example, `r'/-o, .*--output/'` will match `'-o, --out, --output'`.
    - While if you are using substring selector, then it's different. It first tokenizes the option names by `, ` and then search agaist each one with or without the prefix. For example, `'--out'` or `'out'` will match  `'-o, --out, --output'` but `'-out'` will not.

    !!! Hint

        Selectors can be used while removing, selecting, editing and adding before, after an item.


[1]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/help.png
[13]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/theme_blue.png
[14]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/theme_plain.png
[15]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/theme_custom.png
[16]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/helpx.png
