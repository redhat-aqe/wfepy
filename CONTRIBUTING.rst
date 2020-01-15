How to contribute
=================

Thanks for considering contributing to WfEpy.


Reporting issues
----------------

* Under which versions of WfEpy does this happen? Check if this issue is fixed
  in the repository.


Submitting patches
------------------

* Include tests if your patch is supposed to solve a bug, and explain clearly
  under which circumstances the bug happens. Make sure the test fails without
  your patch.
* Follow `PEP8 <http://legacy.python.org/dev/peps/pep-0008/>`_ and
  produce nice code. Code must pass flake8 check.
* For features: Before submitting MR with new feature consider creating RFE
  issue. We want to keep this library as simple as possible so new features
  should be reviewed, signed, etc.


Running the testsuite
^^^^^^^^^^^^^^^^^^^^^

You probably want to set up a `virtualenv
<https://virtualenv.readthedocs.io/en/latest/index.html>`_ and then install all
dendencies by running ``pip install -e .``.

The minimal requirement for running the testsuite is ``py.test`` and ``flake8``
with ``flake8-bugbear`` extension.  You can
install it with::

    pip install pytest flake8 flake8-bugbear

Then you can run the testsuite with::

    pytest
    flake8

For a more isolated test environment, you can also install ``tox`` instead of
``pytest``. You can install it with::

    pip install tox

The ``tox`` command will then run all tests including flake8 and other tests.
