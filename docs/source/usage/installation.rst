Installation Guide
==================

From PyPi
---------
::

    pip install Eventory

Installing Extensions
=====================

Using Inktory
-------------

The Inktory extension requires `pythonnet` to be installed. You can install it using:

::

    pip install pythonnet

or you can use:

::

    pip install Eventory[ink]

*The extra dependencies for "ink" are just `pythonnet`.*

You will also need the `inklecate.exe` and `ink-engine.dll` (`Download from GitHub`__) files in order to run the Eventories.
`inklecate.exe` will be used to compile ink to the runtime format (If you don't install it you won't be able to run Eventories with raw ink content) and `ink-engine.dll` is absolutely needed to play the ink.
You should place both files in the **working directory** of your project so Inktory can find them.

.. __: https://github.com/inkle/ink/releases

Using Discord
-------------

In order to use the Discord extension all you need is the `discord.py` library.