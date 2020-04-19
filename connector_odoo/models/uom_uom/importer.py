# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo.addons.component.core import Component

from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class UomBatchImporter(Component):
    _name = 'odoo.uom.uom.batch.importer'
    _inherit = 'odoo.delayed.batch.importer'
    _apply_on = ['odoo.uom.uom']

    def run(self, filters=None):
        """ Run the synchronization """
        external_ids = self.backend_adapter.search(filters,)
        for external_id in external_ids:
            job_options = {
                'priority': 15,
            }
            self._import_record(external_id, job_options=job_options)


class UomMapper(Component):
    _name = 'odoo.uom.uom.mapper'
    _inherit = 'odoo.import.mapper'
    _apply_on = 'odoo.uom.uom'

    direct = [('name', 'name'),
              ('factor_inv', 'factor_inv'),
              ('factor', 'factor'),
              ('uom_type', 'uom_type'),
              ]

    # TODO: Improve and check family, factor etc...

    @mapping
    def category_id(self, record):
        category_id = record['category_id']
        return {'category_id': category_id.id}

    @only_create
    @mapping
    def check_uom_exists(self, record):
        res = {}
        category_id = record['category_id'].id
        lang = self.backend_record.default_lang_id.code \
            or self.env.user.lang or self.env.context['lang'] or 'en_US'
        _logger.debug("CHECK ONLY CREATE UOM %s with lang %s" % (
            record['name'], lang))

        local_uom_id = self.env['uom.uom'].with_context(
            lang=lang).search([('name', '=', record.name),
                               ('category_id', '=', category_id)])
        _logger.debug('UOM found for %s : %s' % (record, local_uom_id))
        if len(local_uom_id) == 1  :
            res.update({'odoo_id': local_uom_id.id})
        return res


class UoMImporter(Component):
    """ Import Odoo UOM """

    _name = 'odoo.uom.uom.importer'
    _inherit = 'odoo.importer'
    _apply_on = 'odoo.uom.uom'
