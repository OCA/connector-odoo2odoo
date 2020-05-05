# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class SaleOrderBatchImporter(Component):
    """ Import the Odoo Sale Orders.

    For every sale order in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level pricelist imported first.
    """
    _name = 'odoo.sale.order.batch.importer'
    _inherit = 'odoo.delayed.batch.importer'
    _apply_on = ['odoo.sale.order']
    _usage = 'batch.importer'

    def _import_record(self, external_id, job_options=None):
        """ Delay a job for the import """
        super(SaleOrderBatchImporter, self)._import_record(
            external_id, job_options=job_options
        )

    def run(self, filters=None):
        """ Run the synchronization """

        updated_ids = self.backend_adapter.search(filters)

        base_priority = 10
        for order in updated_ids:
            order_id = self.backend_adapter.read(order)
            job_options = {
                'priority': base_priority,
            }
            self._import_record(
                order_id.id, job_options=job_options)


class SaleOrderImporter(Component):
    _name = 'odoo.sale.order.importer'
    _inherit = 'odoo.importer'
    _apply_on = ['odoo.sale.order']

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        for record_partner in [
                self.odoo_record.partner_id,
                self.odoo_record.partner_shipping_id,
                self.odoo_record.partner_invoice_id,
        ]:
            partner = self._get_partner(record_partner)
            bind_partner = self.binder.to_internal(partner, wrap=False)
            print(bind_partner)
            if not bind_partner:
                self._import_dependency(partner, "odoo.res.partner")

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        """
        self.env['sale.order.item'].unlink(
            binding.odoo_id.item_ids.filtered(lambda i: not i.bind_ids))
        """


class SaleOrderImportMapper(Component):
    _name = 'odoo.sale.order.import.mapper'
    _inherit = 'odoo.import.mapper'
    _apply_on = 'odoo.sale.order'

    direct = [
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        order = self.env['sale.order'].search(
            [('name', '=', record.client_order_ref)])
        _logger.debug(
            'found sale order %s for record %s' % (record.name, record))
        if len(order) == 1:
            return {'odoo_id': order.id}
        return {}

    @mapping
    def pricelist_id(self, record):
        binder = self.binder_for('odoo.product.pricelist')
        pricelist_id = binder.to_internal(
            record.pricelist_id, wrap=True)
        return {"pricelist_id": pricelist_id}

    @mapping
    def partner_id(self, record):
        binder = self.binder_for('odoo.res.partner')
        return {
            'partner_id': binder.to_internal(
                record.partner_id, wrap=True),
            'partner_invoice_id': binder.to_internal(
                record.partner_invoice_id, wrap=True),
            'partner_shipping_id': binder.to_internal(
                record.partner_shipping_id, wrap=True),
        }


class SaleOrderLineBatchImporter(Component):
    """ Import the Odoo Sale Order Lines.

    For every pricelist item in the list, a delayed job is created.
    """
    _name = 'odoo.sale.order.batch.importer'
    _inherit = 'odoo.delayed.batch.importer'
    _apply_on = ['odoo.sale.order.item']

    def _import_record(self, external_id, job_options=None):
        """ Delay a job for the import """
        super(SaleOrderLineBatchImporter, self)._import_record(
            external_id, job_options=job_options
        )

    def run(self, filters=None):
        """ Run the synchronization """

        updated_ids = self.backend_adapter.search(filters)

        for order in updated_ids:
            order_id = self.backend_adapter.read(order)
            job_options = {
                'priority': 10,
            }
            self._import_record(order_id.id, job_options=job_options)


class SaleOrderLineImporter(Component):
    _name = 'odoo.sale.order.item.importer'
    _inherit = 'odoo.importer'
    _apply_on = ['odoo.sale.order.item']


class SaleOrderLineImportMapper(Component):
    _name = 'odoo.sale.order.line.import.mapper'
    _inherit = 'odoo.import.mapper'
    _apply_on = 'odoo.sale.order.line'

    direct = [
        ("name", "name"),
        ("price_unit", "price_unit"),
        ("product_uom_qty", "product_uom_qty"),
    ]

    @mapping
    def product_id(self, record):
        binder = self.binder_for('odoo.product.product')
        return {
            'product_id': binder.to_internal(
                record.product_id, wrap=True),
        }
