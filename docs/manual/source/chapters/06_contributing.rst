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
CharLib is composed of two main components:

* The ``liberty`` module: A collection of tools for building and manipulating Liberty files. This
  facilitates the creation of Liberty ``Group``s and ``Attribute``s and adheres closely to the
  Liberty User Guide.
* The ``characterizer`` module: A set of tools for running spice simulations against standard cells.
  This includes tools for managing collections of standard cells and dispatching simulation jobs,
  as well as simulation procedures for characterizing cells.

If you have questions about where to direct your efforts for a particular task, please reply to the
relevant issue or reach out to one of the contacts listed under :ref:`Points-of-Contact`.

Regression Tests
----------------------------------------------------------------------------------------------------

Regression tests are run automatically when you push your code to GitHub. You can also run tests
locally using ``pytest``.

To run all regression tests locally, simply run ``pytest`` from the root directory of your cloned
CharLib repository.

.. note::
    Tests are not available to run locally if you installed CharLib from pip without cloning the
    git repository.

Procedure for Code Contributions
----------------------------------------------------------------------------------------------------

1. Identify an existing issue that you want to solve, or
   `create a new issue <https://github.com/stineje/CharLib/issues/new/>`_.
2. Fork the CharLib repository and make changes to fix the identified issue.
3. Open a draft Pull Request as early as possible in the process. This helps us work as a team and
   work out potential issues ahead of time.
4. Extensively test your changes. This should include creating a regression test that proves the
   issue is solved with your fix.
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
* If your PR targets a specific issue:
    * Add ``Fixes #[issue number]`` to the pull request description or commit message. See the
      `github docs <https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue>`_
      for more information.
    * Make sure your PR includes a regression test demonstrating that the issue is fixed.

Python Code
----------------------------------------------------------------------------------------------------
Python code submissions should adhere to the guidelines in `PEP 8 <https://peps.python.org/pep-0008/>`_.
Aim for improved readability over conciseness. We aren't super strict on this - just make sure your
code is formatted in a reasonable manner.

