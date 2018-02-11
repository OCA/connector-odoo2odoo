.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================
Odoo 2 Odoo Connector
=====================

This module serves as Odoo 2 Odoo connector base. 
[WIP]For specific use-cases (e.g. Intercompany, PO2SO, ...) see the specific modules in this repository.

Installation
============

To install this module, you need to :

* install the [Odoo Connector framework](https://github.com/OCA/connector)
* install the Python Package [OdooRPC](https://pypi.python.org/pypi/OdooRPC/)

More generally, check oca_dependencies.txt and requirements.txt inside the repository

Configuration
=============

To configure this module, you need to:

#. Connector > Odoo > Backend
#. Adapt the info to your external instances
#. Synchronize metadata will import UOM, Attributes and Attribute Values 

To export Product, you need to select product variants (Not template) and 
use add backend action to select on which backend you want to export.
Afterwards, you'll be able to export the product in the other Odoo


.. figure:: path/to/local/image.png
   :alt: alternative description
   :width: 600 px

Usage
=====

Depending on the configuration and the scenario the connector will 

* export and create new / update objects (product, partner, etc.) in the respective intercompany target (backend)
* import and create new / update existing objects

Known issues / Roadmap
======================

* ...

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/connector-odoo2odoo/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Malte Jacobi <malte.jacobi@htwsaar.de>
* Yelizariev Team (https://github.com/it-projects-llc)
* Florent THOMAS (https://mind-and-go.com)

Do not contact contributors directly about support or help with technical issues.

Funders
-------

The development of this module has been financially supported by:

* Company 1 name
* Company 2 name

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
