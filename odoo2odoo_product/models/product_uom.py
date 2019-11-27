# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from openerp import models, fields

from openerp.addons.odoo2odoo_backend.backend import odoo

from ..consumer import OdooSyncExporter

logger = logging.getLogger(__name__)


class ProductUom(models.Model):
    _name = 'product.uom'
    _inherit = ['product.uom']

    odoo_bind_ids = fields.One2many(
        'odoo.product.uom',
        inverse_name='odoo_id',
        string=u"Odoo Bindings",
        readonly=True)


class OdooProductUom(models.Model):
    _name = 'odoo.product.uom'
    _inherit = 'odoo.binding'
    _inherits = {'product.uom': 'odoo_id'}

    odoo_id = fields.Many2one(
        'product.uom',
        string=u"UoM",
        required=True,
        ondelete='cascade')


@odoo(replacing=OdooSyncExporter)
class OdooProductUomExporter(OdooSyncExporter):
    _model_name = 'odoo.product.uom'

    def match_external_record(self, binding):
        """Try to match the local UoM with a remote one."""
        # Get all languages supported and ensure that 'en_US' is the last one
        # (last resort value if we do not find the corresponding translated
        # UoM, less error prones)
        lang_codes = self.env['res.lang'].search([]).mapped('code')
        lang_codes.pop(lang_codes.index('en_US'))
        lang_codes.append('en_US')
        # Try to find a remote UoM corresponding to the local one
        for lang_code in lang_codes:
            record_name = binding.with_context(lang=lang_code).name
            logger.info(u"%s - Try to match the UoM '%s' (lang='%s')...",
                        self.backend_record.name, record_name, lang_code)
            self.backend_adapter.odoo_session.env.context['lang'] = lang_code
            external_ids = self.backend_adapter.search(
                [('name', '=', record_name),
                 '|', ('active', '=', True), ('active', '=', False)])
            # Exclude record IDs already bound
            already_bound_external_ids = self.env[self._model_name].search(
                [('external_odoo_id', 'in', external_ids)]).mapped(
                    'external_odoo_id')
            external_ids = [id_ for id_ in external_ids
                            if id_ not in already_bound_external_ids]
            external_id = external_ids and external_ids[0] or False
            if external_id:
                data = self.backend_adapter.read([external_id], ['name'])[0]
                logger.info(u"%s - UoM '%s' (ID=%s) matches with "
                            u"the external UoM '%s' (ID=%s)",
                            self.backend_record.name,
                            record_name, binding.odoo_id.id,
                            data['name'], external_id)
                binding.with_context(
                    connector_no_export=True).external_odoo_id = external_id
                break
        self.backend_adapter.odoo_session.env.context.clear()
