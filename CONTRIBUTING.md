# Contributing to CharLib
Thanks for your interest in contributing to CharLib! We're always looking for new ideas and ways to improve.

This document is a set of guidelines for how to contribute to CharLib. These are mostly guidelines, not strict rules; you should use your best judgment, and feel free to suggest improvements to this document.

## Using CharLib to Characterize Standard Cells
Looking for information on how to use CharLib? Check out the [README](https://github.com/stineje/CharLib/blob/main/README.md), which has helpful links to detailed usage information.

If you still need additional help, [reach out to one of us](#points-of-contact). We're constantly looking for ways to improve documentation, and your feedback is a big help.

## Getting Started

### Things to Know
CharLib is composed of three main components:

* The `liberty` module: An object-based Python interface for writing standard cell libraries to liberty files. This includes objects to manage standard cell libraries and represent individual combinational and sequential cells.
* The `characterizer` module: A set of tools for running spice simulations against standard cells. This includes tools for managing collections of standard cells and dispatching simulation jobs, as well as simulation procedures for characterizing cells.
* `charlib`: A command-line tool that facilitates interaction with the `characterizer` and `liberty` components. This is the primary user interface for CharLib.

If you have questions about where to direct your efforts for a particular task, please reach out to one of the contacts listed [here](#points-of-contact) or [open an issue](https://github.com/stineje/CharLib/issues/new/).

### Setting up your Development Environment
To get started, you'll need to install a few prerequisites:

* Python version 3.10 or later
* ngspice version 48 or later

After installing those, you should fork the CharLib repository and clone your fork:

```sh
git clone https://github.com/your-username-here/CharLib
cd CharLib
```

We recommend creating a virtual Python environment at this stage to keep development packages
separated from the rest of your system. This is optional, but may save you a lot of headache
later. The following commands create and activate a virtual environment named ".venv".

```sh
python -m venv .venv
source .venv/bin/activate # Or .venv/Scripts/Activate.ps1 for Windows Powershell. See https://docs.python.org/3/library/venv.html#how-venvs-work
```

Now you can install CharLib. Using the `-e` flag will let you see any edits you make without reinstalling.

```sh
# Install our customized version of PySpice
pip install git+https://github.com/infinitymdm/PySpice

# Install your forked version of CharLib
pip install -e .
```

To make sure everything is set up correctly, run `make osu350` to test CharLib with a simple OSU350
characterization task. This will download the OSU350 cells and run characterization on several of
them.

### Procedure for Code Contributions
1. Identify an existing issue that you want to solve, or [create a new issue](https://github.com/stineje/CharLib/issues/new/).
2. Fork the CharLib repository and make changes to fix the identified issue.
3. Open a draft Pull Request as early as possible in the process. This helps us work as a team and work out potential issues ahead of time.
4. Extensively test your changes.
5. Once you're done making changes, mark your PR as ready for review. Maintainers will review your code and accept your PR or request changes as needed.

## Reporting Issues
Bugs can be reported by [opening a new Issue here](https://github.com/stineje/CharLib/issues/new/). Include as much detail as possible. If feasible, attach your CharLib configuration files and cells to the Issue so that we can identify what went wrong.

## Requesting New Features
Feature requests can be made by [opening a new Issue here](https://github.com/stineje/CharLib/issues/new/). Include as much detail as possible about how you want to use CharLib and/or how you think it should behave.

## Style Guidelines

### Git Commit Messages
* Use present tense ("Fix bug", not "Fixed bug")
* Use imperative mood ("Replace thingamajig", not "Replaces thingamajig")
* Limit the first line to 72 characters or less
* Reference issues, pull requests, and other information liberally after the first line
    * If the first line isn't enough to explain the full scope of your changes, use as much extra space as needed.

### Pull Request Guidelines
* Pull Requests should be concise and focused. Smaller changesets are much easier to implement and review than large changes. Keeping PRs small also helps us limit scope creep.
* Provide a detailed description of changes. Add as much context and rational for your decision-making process as possible.
* Add 'Fixes #[issue number]' to the pull request description or commit message if your PR targets a specific issue. See the [github docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue) for more information.

### Python Code
Python code submissions should adhere to the guidelines in [PEP 8](https://peps.python.org/pep-0008/). Aim for improved readability over conciseness. We aren't super strict on this - just make sure your code is formatted in a reasonable manner.

## Points of Contact
If you have any other questions, please reach out to one of us:
* Marcus Mellor: marcus@infinitymdm.dev
* Dr. James Stine: james.stine@okstate.edu
