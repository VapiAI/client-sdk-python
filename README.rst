===============
Vapi Python SDK
===============


.. image:: https://img.shields.io/pypi/v/vapi_python.svg
        :target: https://pypi.python.org/pypi/vapi_python

.. image:: https://img.shields.io/travis/jordan.cde/vapi_python.svg
        :target: https://travis-ci.com/jordan.cde/vapi_python

.. image:: https://readthedocs.org/projects/vapi-python/badge/?version=latest
        :target: https://vapi-python.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


This package lets you start Vapi calls directly from Python.

Installation
------------

You can install the package via pip:

.. code-block:: bash

   pip install vapi_python

Usage
-----

First, import the Vapi class from the package:

.. code-block:: python

   from vapi_python import Vapi

Then, create a new instance of the Vapi class, passing your API Key as a parameter to the constructor:

.. code-block:: python

   vapi = Vapi(api_key='your-api-key')

You can start a new call by calling the `start` method and passing an `assistant` object or `assistantId`. You can find the available options here: `docs.vapi.ai <https://docs.vapi.ai/api-reference/assistants/create-assistant>`

.. code-block:: python

   vapi.start(assistant_id='your-assistant-id')

or

.. code-block:: python

   assistant = {
     'firstMessage': 'Hey, how are you?',
     'context': 'You are a shopping assistant...',
     'model': 'gpt-3.5-turbo',
     'voice': 'jennifer-playht',
     "recordingEnabled": True,
     "interruptionsEnabled": False,
     "functions": [
       {
         "name": "setColor",
         "description": "Used to set the color",
         "parameters": { 
             "type": "object",
             "properties": { 
                 "color": { 
                 "type": "string" 
                 } 
             }
         }
       }
     ]
   }

   vapi.start(assistant=assistant)

The `start` method will initiate a new call.

You can also override existing assistant parameters or set variables with the `assistant_overrides` parameter:

.. code-block:: python

   # Assume the below has already been set for the assistant with ID 'your-assistant-id'
   assistant = {
      'firstMessage': 'Hey, {{name}} how are you?',
   }

   assistant_overrides = {
      "recordingEnabled": False,
      "variableValues": {
         "name": "John"
      }
   }

   vapi.start(assistant_id='your-assistant-id', assistant_overrides=assistant_overrides)

You can stop the session by calling the `stop` method:

.. code-block:: python

   vapi.stop()

This will stop the recording and close the connection.

License
-------

MIT License

Copyright (c) 2023 Vapi Labs Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

