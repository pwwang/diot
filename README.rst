

.. image:: https://raw.githubusercontent.com/pwwang/diot/master/logo.png
   :target: https://raw.githubusercontent.com/pwwang/diot/master/logo.png
   :alt: Logo


`
.. image:: https://img.shields.io/pypi/v/diot?style=flat-square
   :target: https://img.shields.io/pypi/v/diot?style=flat-square
   :alt: pypi
 <https://pypi.org/project/diot/>`_ `
.. image:: https://img.shields.io/github/tag/pwwang/diot?style=flat-square
   :target: https://img.shields.io/github/tag/pwwang/diot?style=flat-square
   :alt: tag
 <https://github.com/pwwang/diot>`_ `
.. image:: https://img.shields.io/codacy/grade/f19cfbaa23d442d6ae20af66a4cf6796?style=flat-square
   :target: https://img.shields.io/codacy/grade/f19cfbaa23d442d6ae20af66a4cf6796?style=flat-square
   :alt: codacy quality
 <https://app.codacy.com/project/pwwang/diot/dashboard>`_ `
.. image:: https://img.shields.io/codacy/coverage/f19cfbaa23d442d6ae20af66a4cf6796?style=flat-square
   :target: https://img.shields.io/codacy/coverage/f19cfbaa23d442d6ae20af66a4cf6796?style=flat-square
   :alt: coverage
 <https://app.codacy.com/project/pwwang/diot/dashboard>`_ 
.. image:: https://img.shields.io/pypi/pyversions/diot?style=flat-square
   :target: https://img.shields.io/pypi/pyversions/diot?style=flat-square
   :alt: pyver
 
.. image:: https://img.shields.io/github/workflow/status/pwwang/diot/Build%20and%20Deploy?style=flat-square
   :target: https://img.shields.io/github/workflow/status/pwwang/diot/Build%20and%20Deploy?style=flat-square
   :alt: building
 
.. image:: https://img.shields.io/github/workflow/status/pwwang/diot/Build%20Docs?label=docs&style=flat-square
   :target: https://img.shields.io/github/workflow/status/pwwang/diot/Build%20Docs?label=docs&style=flat-square
   :alt: docs


Python dictionary with dot notation (A re-implementation of `python-box <https://github.com/cdgriffith/Box>`_ with some issues fixed and simplified)

.. code-block:: python

   from diot import Diot

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
   movie_diot = Diot(movie_data)

   movie_diot.movies.Robin_Hood_Men_in_Tights.imdb_stars
   # 6.7

   movie_diot.movies.Spaceballs.stars[0].name
   # 'Mel Brooks'

   # Different as box, you have to use Diot for new data in a list
   movie_diot.movies.Spaceballs.stars.append(
       Diot({"name": "Bill Pullman", "imdb": "nm0000597", "role": "Lone Starr"}))
   movie_diot.movies.Spaceballs.stars[-1].role
   # 'Lone Starr'

Install
-------

.. code-block:: shell

   pip install diot

API
---

https://pwwang.github.io/diot/api/diot/

Diot
----

Instantiated the same ways as ``dict``

.. code-block:: python

   Diot({'data': 2, 'count': 5})
   Diot(data=2, count=5)
   Diot({'data': 2, 'count': 1}, count=5)
   Diot([('data', 2), ('count', 5)])

   # All will create
   # Diot([('data', 2), ('count', 5)], diot_nest = True, diot_transform = 'safe')

Same as ``python-box``\ , ``Diot`` is a subclass of dict which overrides some base functionality to make sure everything stored in the dict can be accessed as an attribute or key value.

.. code-block:: python

   diot = Diot({'data': 2, 'count': 5})
   diot.data == diot['data'] == getattr(diot, 'data')

By default, diot uses a safe transformation to transform keys into safe names that can be accessed by ``diot.xxx``

.. code-block:: python

   dt = Diot({"321 Is a terrible Key!": "yes, really"})
   dt._321_Is_a_terrible_Key_
   # 'yes, really'

Different as ``python-box``\ , duplicate attributes are not allowed.

.. code-block:: python

   dt = Diot({"!bad!key!": "yes, really", ".bad.key.": "no doubt"})
   # KeyError

Use different transform functions:

.. code-block:: python

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

Use your own transform function:

.. code-block:: python

   import inflection

   dt = Diot(post = 10, diot_transform = inflection.pluralize)
   dt.posts == dt['posts'] == dt['post'] == 10

OrderedDiot
-----------

.. code-block:: python

   diot_of_order = OrderedDiot()
   diot_of_order.c = 1
   diot_of_order.a = 2
   diot_of_order.d = 3

   list(diot_of_order.keys()) == ['c', 'a', 'd']

   # insertion allowed for OrderedDiot
   od = OrderedDiot()
   od.insert(0, "c", "d")
   od.insert(None, "x", "y")
   od.insert_before('c', "e", "f")
   od.insert_after("a", ("g", "h"))

   od2 = OrderedDiot()
   od2.a1 = 'b1'
   od2.c1 = 'd1'
   od.insert(-1, od2)

   od3 = OrderedDiot()
   od3.a2 = 'b2'
   od3.c2 = 'd2'
   od.insert_before('c', od3)
