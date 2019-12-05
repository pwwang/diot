![Logo](https://raw.githubusercontent.com/pwwang/diot/master/logo.png)

Python dictionary with dot notation

[![pypi][1]][2] [![tag][3]][4] [![travis][5]][6] [![codacy quality][7]][8] [![codacy quality][9]][8] ![pyver][10]

- Partially compartible with `python-box`
- Issue #87 of `python-box` fixed
- Nest conversion of inside `dict/list` turned off
- Customization of key conversion

```python
from diot import Diot, NestDiot

movie_data = {
  "movies": {
    "Spaceballs": {
      "imdb stars": 7.1,
      "rating": "PG",
      "length": 96,
      "director": "Mel Brooks",
      "stars": [{"name": "Mel Brooks", "imdb": "nm0000316", "role": "President Skroob"},
                {"name": "John Candy","imdb": "nm0001006", "role": "Barf"},
                {"name": "Rick Moranis", "imdb": "nm0001548", "role": "Dark Helmet"}
      ]
    },
    "Robin Hood: Men in Tights": {
      "imdb stars": 6.7,
      "rating": "PG-13",
      "length": 104,
      "director": "Mel Brooks",
      "stars": [
                {"name": "Cary Elwes", "imdb": "nm0000144", "role": "Robin Hood"},
                {"name": "Richard Lewis", "imdb": "nm0507659", "role": "Prince John"},
                {"name": "Roger Rees", "imdb": "nm0715953", "role": "Sheriff of Rottingham"},
                {"name": "Amy Yasbeck", "imdb": "nm0001865", "role": "Marian"}
      ]
    }
  }
}

# Box is a conversion_box by default, pass in `conversion_box=False` to disable that behavior
# Explicitly tell Diot to convert dict/list inside
movie_diot = Diot(movie_data, diot_nest = True)
# or movie_diot = NestDiot(movie_data)

movie_diot.movies.Robin_Hood_Men_in_Tights.imdb_stars
# 6.7

movie_diot.movies.Spaceballs.stars[0].name
# 'Mel Brooks'

# Different as box, you have to use Diot for new data in a list
movie_diot.movies.Spaceballs.stars.append(
	Diot({"name": "Bill Pullman", "imdb": "nm0000597", "role": "Lone Starr"}))
movie_diot.movies.Spaceballs.stars[-1].role
# 'Lone Starr'
```

## Install
```shell
pip install diot
```

## Diot

Instantiated the same ways as `dict`
```python
Diot({'data': 2, 'count': 5})
Diot(data=2, count=5)
Diot({'data': 2, 'count': 1}, count=5)
Diot([('data', 2), ('count', 5)])

# All will create
# Diot([('data', 2), ('count', 5)], diot_nest = False, diot_transform = 'safe')
```

Same as `python-box`, `Diot` is a subclass of dict which overrides some base functionality to make sure everything stored in the dict can be accessed as an attribute or key value.

```python
diot = Diot({'data': 2, 'count': 5})
diot.data == diot['data'] == getattr(diot, 'data')
```

By default, diot uses a safe transformation to transform keys into safe names that can be accessed by `diot.xxx`
```python
dt = Diot({"321 Is a terrible Key!": "yes, really"})
dt._321_Is_a_terrible_Key_
# 'yes, really'
```

Different as `python-box`, duplicate attributes are not allowed.
```python
dt = Diot({"!bad!key!": "yes, really", ".bad.key.": "no doubt"})
# KeyError
```

Use different transform functions:

```python
dt = Diot(oneTwo = 12, diot_transform = 'snake_case')
# or use alias:
# dt = SnakeDiot(oneTwo = 12)
dt.one_two == dt['one_two'] == dt['oneTwo'] == 12

dt = Diot(one_two = 12, diot_transform = 'camel_case')
# or use alias:
# dt = CamelDiot(one_two = 12)
dt.oneTwo == dt['one_two'] == dt['oneTwo'] == 12

dt = Diot(one_two = 12, diot_transform = 'upper')
dt.ONE_TWO == dt['one_two'] == dt['ONETWO'] == 12

dt = Diot(ONE_TWO = 12, diot_transform = 'lower')
dt.one_two == dt['ONE_TWO'] == dt['one_two'] == 12
```

Use your own transform function:

```python
import inflection

dt = Diot(post = 10, diot_transform = inflection.pluralize)
dt.posts == dt['posts'] == dt['post'] == 10
```

## OrderedDiot
```python
diot_of_order = OrderedDiot()
diot_of_order.c = 1
diot_of_order.a = 2
diot_of_order.d = 3

list(diot_of_order.keys()) == ['c', 'a', 'd']
```

[1]: https://img.shields.io/pypi/v/diot?style=flat-square
[2]: https://pypi.org/project/diot/
[3]: https://img.shields.io/github/tag/pwwang/diot?style=flat-square
[4]: https://github.com/pwwang/diot
[5]: https://img.shields.io/travis/pwwang/diot?style=flat-square
[6]: https://travis-ci.org/pwwang/diot
[7]: https://img.shields.io/codacy/grade/f19cfbaa23d442d6ae20af66a4cf6796?style=flat-square
[8]: https://app.codacy.com/project/pwwang/diot/dashboard
[9]: https://img.shields.io/codacy/coverage/f19cfbaa23d442d6ae20af66a4cf6796?style=flat-square
[10]: https://img.shields.io/pypi/pyversions/diot?style=flat-square