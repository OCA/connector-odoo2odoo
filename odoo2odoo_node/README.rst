.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

================
Odoo2Odoo - Node
================

This module is required on all *Odoo* instances synchronized by an *Odoo*
backend (see the ``odoo2odoo_backend`` module).

It simply adds new CRUD methods similar to ``create``, ``read``, ``write``
and ``unlink`` to focus on the data and avoid undesirable behavior (custom
overloads of the standard methods). These new methods are then used by the
``odoo2odoo_backend`` module to drive the synchronization.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Sébastien Alix <sebastien.alix@osiell.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
