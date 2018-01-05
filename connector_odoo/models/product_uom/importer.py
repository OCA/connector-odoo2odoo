# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo.addons.component.core import Component

from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)

class ProductUomMapper(Component):
    _name = 'odoo.product.uom.mapper'
    _inherit = 'odoo.import.mapper'
    _apply_on = 'odoo.product.uom'

    direct = [('name', 'name')]

    @only_create
    @mapping
    def check(self, record):
        # partners are companies so we can bind
        # addresses on them
        _logger.info('Checking the UOM correspondances')
        return {'odoo_id': partner.id}
    