***************************************************************************************************
Contributing
***************************************************************************************************

Thanks for your interest in contributing to CharLib! We're always looking for new ideas and ways to
improve.

This chapter is a set of guidelines on how to contribute to CharLib. These are mostly guidelines,
not strict rules; you should use your best judgment, and feel free to suggest improvements to this
document.

====================================================================================================
Reporting Issues
====================================================================================================

Bugs can be reported by `opening a new issue here <https://github.com/stineje/CharLib/issues/new?template=problem-report.md>`_.
Include as much detail as possible. If feasible, attach your CharLib configuration files and cells
to the issue so that we can identify what went wrong.

====================================================================================================
Requesting New Features
====================================================================================================
Feature requests can be made by `opening a new issue here <https://github.com/stineje/CharLib/issues/new?template=feature_request.md>`_.
Include as much detail as possible about how you want to use CharLib and/or how you think it should
behave.

====================================================================================================
Code Contributions
====================================================================================================

Things to Know Before Contributing
----------------------------------------------------------------------------------------------------
CharLib is composed of three main components:

* The ``liberty`` module: An object-based Python interface for writing standard cell
  libraries to liberty files. This includes objects to manage standard cell libraries and
  represent individual combinational and sequential cells.
* The ``characterizer`` module: A set of tools for running spice simulations against standard cells.
  This includes tools for managing collections of standard cells and dispatching simulation jobs,
  as well as simulation procedures for characterizing cells.
* ``charlib``: A command-line tool that facilitates interaction with the ``characterizer`` and
  ``liberty`` components. This is the primary user interface for CharLib.

If you have questions about where to direct your efforts for a particular task, please reply to the
relevant issue or reach out to one of the contacts listed under:ref:`Points-of-Contact`.

Running tests
----------------------------------------------------------------------------------------------------

To run tests execute

.. code-block:: SHELL

    make osu350

to test CharLib with a simple OSU350 characterization task. This will download the OSU350 cells and
run characterization on several of them.

.. note::
    Tests are only available when CharLib is installed from a cloned git repository. If you
    installed CharLib from a cloned repository, running tests is a great way to make sure you have
    installed CharLib correctly.

.. note::
    If you get PySpice errors in the file "PySpice/Spice/NgSpice/SimulationType.py", the most
    likely culprit is that PySpice hasn't yet been validated against the version of ngspice that
    you have installed. The latest validated version is found in the PySpice code
    `here <https://github.com/infinitymdm/PySpice/blob/master/PySpice/Spice/NgSpice/SimulationType.py#L85>`_.

Procedure for Code Contributions
----------------------------------------------------------------------------------------------------

1. Identify an existing issue that you want to solve, or
   `create a new issue <https://github.com/stineje/CharLib/issues/new/>`_.
2. Fork the CharLib repository and make changes to fix the identified issue.
3. Open a draft Pull Request as early as possible in the process. This helps us work as a team and
   work out potential issues ahead of time.
4. Extensively test your changes.
5. Once you're done making changes, mark your PR as ready for review. Maintainers will review your
   code and accept your PR or request changes as needed.

====================================================================================================
Style Guidelines
====================================================================================================

Git Commit Messages
----------------------------------------------------------------------------------------------------
* Use present tense ("Fix bug", not "Fixed bug")
* Use imperative mood ("Replace thingamajig", not "Replaces thingamajig")
* Limit the first line to 72 characters or less
* Reference issues, pull requests, and other information liberally after the first line
    * If the first line isn't enough to explain the full scope of your changes, use as much extra
      space as needed.

Pull Request Guidelines
----------------------------------------------------------------------------------------------------
* Pull Requests should be concise and focused. Smaller changesets are much easier to implement and
  review than large changes. Keeping PRs small also helps us limit scope creep.
* Provide a detailed description of changes. Add as much context and rational for your
  decision-making process as possible.
* Add ``Fixes #[issue number]`` to the pull request description or commit message if your PR targets
  a specific issue. See the
  `github docs <https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue>`_
  for more information.

Python Code
----------------------------------------------------------------------------------------------------
Python code submissions should adhere to the guidelines in `PEP 8 <https://peps.python.org/pep-0008/>`_.
Aim for improved readability over conciseness. We aren't super strict on this - just make sure your
code is formatted in a reasonable manner.

