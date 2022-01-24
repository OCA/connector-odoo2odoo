.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================
Odoo 2 Odoo Connector
=====================

This module serves as Odoo 2 Odoo connector base. This connection allows the import and export of information between instances. This scenario may be necessary when considering a progressive version migration or when it is not possible to use `OpenUpgrade <https://github.com/oca/openupgrade>`_ due to company policy. They also thought for specific use-cases (e.g. Intercompany, PO2SO, ...) but there are specific OCA repositories for those purposes.

Currently, a mapping of the following models has been done:

 * ``partner``
 * ``product_attribute``
 * ``product_attribute_value``
 * ``product_category``
 * ``product_pricelist``
 * ``product_product``
 * ``product_template``
 * ``sale_order``
 * ``uom_uom``

Installation
============

To install this module, you need to :

* install the `Odoo Connector framework <https://github.com/OCA/connector>`_
* install the Python Package `OdooRPC <https://pypi.python.org/pypi/OdooRPC>`_

If you will use connection for OpenERP (6.1 and later), you need to install the `oerplib>=0.8.5 <https://github.com/flachica/oerplib>`_. This is a fork whose original code is `here <https://github.com/osiell/oerplib>`_ to which python 3 support has been added.

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

Usage
=====

Depending on the configuration and the scenario the connector will

* export and create new / update objects (product, partner, etc.) in the respective intercompany target (backend)
* import and create new / update existing objects

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
