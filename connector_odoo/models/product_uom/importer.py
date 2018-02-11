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

    direct = [('name', 'name'),
              ('factor_inv', 'factor_inv'),
              ('factor', 'factor'),
              ]

    #TODO: Improve and check family, factor etc...

    @only_create
    @mapping
    def check_uom_exists(self, record):
        res = {}
        _logger.debug("CHECK ONLY CREATE")
        lang = self.backend_record.default_lang_id.code or self.env.user.lang or self.env.context['lang'] or 'en_US'  
        local_uom_id = self.env['product.uom'].with_context(
            lang=lang).search([('name', '=', record.name)])
        _logger.debug('UOM found for %s : %s' % (record, local_uom_id))
        if len(local_uom_id) == 1  :
#             res = local_uom_id.copy_data()[0] #dict((field, value) for field, value in local_uom_id.iteritems())
            res.update({'odoo_id': local_uom_id.id})
        
        return res

class ProductUoMImporter(Component):
    """ Import Odoo UOM """

    _name = 'odoo.product.uom.importer'
    _inherit = 'odoo.importer'
    _apply_on = 'odoo.product.uom'

