.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
Odoo 2 Odoo Connector
=====================

This module serves as Odoo 2 Odoo connector base. For specific use-cases (e.g. Intercompany, PO2SO, ...) see the specific modules in this repository.

Installation
============

To install this module, you need to:

* install the [OpenERP Connector framework](https://github.com/OCA/connector)
* install the Python Package [OERPLib](https://pypi.python.org/pypi/OERPLib/)

Configuration
=============

To configure this module, you need to:

* create and configure a new Backend (Menu -> Connector -> Odoo -> Backends)
* activate the needed cron jobs

Usage
=====

Depending on the configuration and the scenario the connector will 

* export and create new / update objects (product, partner, etc.) in the respective intercompany target (backend)
* import and create new / update existing objects

Known issues / Roadmap
======================

.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/
connector-odoo2odoo/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback `here <https://github.com/OCA/
connector-odoo2odoo/issues/new?body=module:%20
odooconnector_base%0Aversion:%20
8.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Malte Jacobi <malte.jacobi@htwsaar.de>

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
