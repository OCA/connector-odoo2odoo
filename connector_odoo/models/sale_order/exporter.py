# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    mapping,
    ExportMapChild,
)
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
# from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class OdooSaleOrderExporter(Component):
    _name = "odoo.sale.order.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.sale.order"]

    def _get_partner(self, record_partner):
        partner_ids = record_partner.bind_ids
        partner = self.env['odoo.res.partner']
        if partner_ids:
            partner = partner_ids.filtered(
                lambda c: c.backend_id == self.backend_record)
        if not partner:
            partner = self.env['odoo.res.partner'].create({
                'odoo_id': record_partner.id,
                'external_id': 0,
                'backend_id': self.backend_record.id})
        return partner

    def _export_dependencies(self):
        # FIXME: This doesn't seem right
        if not self.binding.partner_id:
            return
        for record_partner in [
                self.binding.partner_id,
                self.binding.partner_shipping_id,
                self.binding.partner_invoice_id,
        ]:
            partner = self._get_partner(record_partner)
            bind_partner = self.binder.to_external(partner, wrap=False)
            if not bind_partner:
                self._export_dependency(partner, "odoo.res.partner")


class SaleOrderExportMapper(Component):
    _name = "odoo.sale.order.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.sale.order"]

    direct = [
    ]

    children = [
        ("order_line", "order_line", "odoo.sale.order.line")
    ]

    @mapping
    def date_order(self, record):
        return {
            'date_order': record.date_order.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT)}

    @mapping
    def pricelist_id(self, record):
        binder = self.binder_for('odoo.product.pricelist')
        pricelist_id = binder.to_external(
            record.pricelist_id, wrap=True)
        return {"pricelist_id": pricelist_id}

    @mapping
    def partner_id(self, record):
        binder = self.binder_for('odoo.res.partner')
        return {
            'partner_id': binder.to_external(
                record.partner_id, wrap=True),
            'partner_invoice_id': binder.to_external(
                record.partner_invoice_id, wrap=True),
            'partner_shipping_id': binder.to_external(
                record.partner_shipping_id, wrap=True),
        }

    @mapping
    def client_order_ref(self, record):
        return {"client_order_ref": record.name}


class SaleOrderLineExportMapper(Component):
    _name = "odoo.sale.order.line.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.sale.order.line"]

    direct = [
        ("name", "name"),
        ("price_unit", "price_unit"),
        ("product_uom_qty", "product_uom_qty"),
    ]

    @mapping
    def product_id(self, record):
        binder = self.binder_for('odoo.product.product')
        return {
            'product_id': binder.to_external(
                record.product_id, wrap=True),
        }


class SaleOrderExportMapChild(ExportMapChild):
    _model_name = 'odoo.sale.order'

    def format_items(self, items_values):
        return [(0, 0, item) for item in items_values]
