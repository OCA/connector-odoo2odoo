# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields

from openerp.addons.odoo2odoo_backend.backend import odoo

from ..consumer import OdooSyncExportMapper


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product']

    odoo_bind_ids = fields.One2many(
        'odoo.product.product',
        inverse_name='odoo_id',
        string=u"Odoo Bindings",
        readonly=True)


class OdooProductProduct(models.Model):
    _name = 'odoo.product.product'
    _inherit = 'odoo.binding'
    _inherits = {'product.product': 'odoo_id'}

    odoo_id = fields.Many2one(
        'product.product',
        string=u"Product",
        required=True,
        ondelete='cascade')


@odoo(replacing=OdooSyncExportMapper)
class OdooProductProductExportMapper(OdooSyncExportMapper):
    _model_name = 'odoo.product.product'

    def odoo2odoo(self, record):
        product_tmpl_id = record.product_tmpl_id.id
        binder = self.binder_for('odoo.product.template')
        external_id = binder.to_backend(product_tmpl_id, wrap=True)
        data = {
            'product_tmpl_id': external_id,
        }
        return data
