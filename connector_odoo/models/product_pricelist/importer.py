# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class ProductPricelistBatchImporter(Component):
    """ Import the Odoo Product Pricelists.

    For every product pricelist in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level pricelist imported first.
    """
    _name = 'odoo.product.pricelist.batch.importer'
    _inherit = 'odoo.delayed.batch.importer'
    _apply_on = ['odoo.product.pricelist']

    def _import_record(self, external_id, job_options=None):
        """ Delay a job for the import """
        super(ProductPricelistBatchImporter, self)._import_record(
            external_id, job_options=job_options
        )

    def run(self, filters=None):
        """ Run the synchronization """

        updated_ids = self.backend_adapter.search(filters)

        base_priority = 10
        for pricelist in updated_ids:
            pricelist_id = self.backend_adapter.read(pricelist)
            job_options = {
                'priority': base_priority + pricelist_id.parent_left or 0,
            }
            self._import_record(
                pricelist_id.id, job_options=job_options)


class ProductPricelistImporter(Component):
    _name = 'odoo.product.pricelist.importer'
    _inherit = 'odoo.importer'
    _apply_on = ['odoo.product.pricelist']

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        pass

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        """
        self.env['product.pricelist.item'].unlink(
            binding.odoo_id.item_ids.filtered(lambda i: not i.bind_ids))
        """


class ProductPricelistImportMapper(Component):
    _name = 'odoo.product.pricelist.import.mapper'
    _inherit = 'odoo.import.mapper'
    _apply_on = 'odoo.product.pricelist'

    direct = [
        ('active', 'active'),
        ('code', 'code'),
        ('discount_policy', 'discount_policy'),
        ('name', 'name'),
        ('selectable', 'selectable'),
        ('sequence', 'sequence'),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        # TODO: Improve the matching on name and position in the tree so that
        # multiple pricelist with the same name will be allowed and not
        # duplicated
        pricelist = self.env['product.pricelist'].search(
            [('name', '=', record.name)])
        _logger.debug(
            'found pricelist %s for record %s' % (pricelist.name, record))
        if len(pricelist) == 1:
            return {'odoo_id': pricelist.id}
        return {}

    @mapping
    def currency_id(self, record):
        if not record.currency_id:
            return
        currency = self.env['res.currency'].search(
            [('name', '=', record.currency_id.name)])
        _logger.debug(
            'found currency %s for record %s' % (currency.name, record))
        if len(currency) == 1:
            return {'currency_id': currency.id}
        raise MappingError("No currency found %s" % currency.name)
        return {}


class ProductPricelistItemBatchImporter(Component):
    """ Import the Odoo Product Pricelist Items.

    For every pricelist item in the list, a delayed job is created.
    """
    _name = 'odoo.product.pricelist.batch.importer'
    _inherit = 'odoo.delayed.batch.importer'
    _apply_on = ['odoo.product.pricelist.item']

    def _import_record(self, external_id, job_options=None):
        """ Delay a job for the import """
        super(ProductPricelistItemBatchImporter, self)._import_record(
            external_id, job_options=job_options
        )

    def run(self, filters=None):
        """ Run the synchronization """

        updated_ids = self.backend_adapter.search(filters)

        for pricelist in updated_ids:
            pricelist_id = self.backend_adapter.read(pricelist)
            job_options = {
                'priority': 10,
            }
            self._import_record(
                pricelist_id.id, job_options=job_options)


class ProductPricelistItemImporter(Component):
    _name = 'odoo.product.pricelist.item.importer'
    _inherit = 'odoo.importer'
    _apply_on = ['odoo.product.pricelist.item']

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.odoo_record
        self._import_dependency(
            record.pricelist_id.id, 'odoo.product.pricelist')
        if record.product_id:
            self._import_dependency(
                record.product_id.id, 'odoo.product.product')
        if record.product_tmpl_id:
            self._import_dependency(
                record.product_tmpl_id.id, 'odoo.product.template')
        if record.categ_id:
            self._import_dependency(
                record.categ_id.id, 'odoo.product.category')
        if record.base_pricelist_id:
            self._import_dependency(
                record.base_pricelist_id.id, 'odoo.product.pricelist')
            filters = [
                ("pricelist_id", "=", record.id),
            ]
            self.env["odoo.product.pricelist.item"].with_delay().import_batch(
                self.backend_record, filters)


class ProductPricelistItemImportMapper(Component):
    _name = 'odoo.product.pricelist.item.import.mapper'
    _inherit = 'odoo.import.mapper'
    _apply_on = 'odoo.product.pricelist.item'

    direct = [
        ('applied_on', 'applied_on'),
        ('base', 'base'),
        ('compute_price', 'compute_price'),
        ('date_end', 'date_end'),
        ('date_start', 'date_start'),
        ('fixed_price', 'fixed_price'),
        ('min_quantity', 'min_quantity'),
        ('name', 'name'),
        ('percent_price', 'percent_price'),
        ('price', 'price'),
        ('price_discount', 'price_discount'),
        ('price_max_margin', 'price_max_margin'),
        ('price_min_margin', 'price_min_margin'),
        ('price_round', 'price_round'),
        ('price_surcharge', 'price_surcharge'),
    ]

    """
    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for('odoo.product.pricelist')
        pricelist = binder.to_internal(record.pricelist_id.id, unwrap=True)
        item = self.env['product.pricelist.item'].search([
            ('applied_on', '=', record.applied_on),
            ('categ_id', '=', record.categ_id.name),
            ('date_start', '=', record.date_start),
            ('date_end', '=', record.date_end),
        ])
        _logger.debug(
            'found pricelist %s for record %s' % (pricelist.name, record))
        if len(pricelist) == 1:
            return {'odoo_id': pricelist.id}
        return {}
    """

    @mapping
    def pricelist_id(self, record):
        binder = self.binder_for('odoo.product.pricelist')
        pricelist = binder.to_internal(record.pricelist_id.id, unwrap=True)
        return {"pricelist_id": pricelist.id}

    @mapping
    def categ_id(self, record):
        if record.categ_id:
            binder = self.binder_for('odoo.product.category')
            categ = binder.to_internal(record.categ_id.id, unwrap=True)
            return {"categ_id": categ.id}

    @mapping
    def base_pricelist_id(self, record):
        if record.base_pricelist_id:
            binder = self.binder_for('odoo.product.pricelist')
            pricelist = binder.to_internal(
                record.base_pricelist_id.id, unwrap=True)
            return {"base_pricelist_id": pricelist.id}

    @mapping
    def product_id(self, record):
        if record.product_id:
            binder = self.binder_for('odoo.product.product')
            product = binder.to_internal(record.product_id.id, unwrap=True)
            return {"product_id": product.id}
        return {}

    @mapping
    def product_tmpl_id(self, record):
        if record.product_tmpl_id:
            binder = self.binder_for('odoo.product.template')
            product = binder.to_internal(
                record.product_tmpl_id.id, unwrap=True)
            return {"product_tmpl_id": product.id}
        return {}
