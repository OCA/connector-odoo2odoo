# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class MetadataBatchImporter(Component):
    """ Import the records directly, without delaying the jobs.

    Import the Odoo Minimal Datas :
    * UOM
    * Product categories
    * Product attributes and theirs values

    They are imported directly because this is a rare and fast operation,
    and we don't really bother if it blocks the UI during this time.
    (that's also a mean to rapidly check the connectivity with Odoo).

    """

    _name = 'odoo.metadata.batch.importer'
    _inherit = 'odoo.direct.batch.importer'
    _apply_on = [
        'odoo.product.uom',
#         'odoo.product.category',
        'odoo.product.attribute',
        'odoo.product.attribute.value'
    ]
    
#     _usage = 'batch.importer'
    
