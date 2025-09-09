This folder contains python tools for interfacing with liberty files.

The core of this module is liberty.py, which defines several classes for constructing and
manipulating liberty statements. This is closely based on Chapter 1 of the Liberty User Guide
Volume 1.

Additional features are added through library.py, which defines more practical tools for
constructing liberty libraries. The classes defined therein inherit from liberty.Group, but have
helpful changes to formatting or data access.

CharLib uses this module to construct liberty objects from cell descriptions and liberty results.
