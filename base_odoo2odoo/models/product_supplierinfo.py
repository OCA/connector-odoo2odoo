# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector.unit.mapper import ImportMapper, ExportMapper
from ..unit.import_synchronizer import (IntercompanyImporter,
                                        DirectBatchImporter)
from ..unit.mapper import (IntercompanyImportMapChild,
                           IntercompanyExportMapChild)
from ..unit.backend_adapter import IntercompanyAdapter
from ..backend import ic_odoo


_logger = logging.getLogger(__name__)


class IntercompanyProductSupplierInfo(models.Model):
    _name = 'intercompany.product.supplierinfo'
    _inherit = 'intercompany.binding'
    _inherits = {'product.supplierinfo': 'openerp_id'}
    _description = 'Intercompany Product Supplierinfo'

    openerp_id = fields.Many2one(
        comodel_name='product.supplierinfo',
        string='Supplierinfo',
        required=True,
        ondelete='restrict'
    )


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    ic_bind_ids = fields.One2many(
        comodel_name='intercompany.product.supplierinfo',
        inverse_name='openerp_id',
        string='Intercompany Binding'
    )


"""
I M P O R T
"""


@ic_odoo
class ProductSupplierInfoBatchImporter(DirectBatchImporter):
    _model_name = ['intercompany.product.supplierinfo']


@ic_odoo
class ProductSupplierInfoImporter(IntercompanyImporter):
    _model_name = ['intercompany.product.supplierinfo']


@ic_odoo
class ProductSupplierInfoImportMapper(ImportMapper):
    _model_name = ['intercompany.product.supplierinfo']

    _map_child_class = IntercompanyImportMapChild

    direct = [('sequence', 'sequence'), ('product_name', 'product_name'),
              ('product_code', 'product_code'), ('min_qty', 'min_qty'),
              ('delay', 'delay')]

    children = [
        ('pricelist_ids', 'pricelist_ids', 'pricelist.partnerinfo')
    ]

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        source = map_record.source
        child_records = source[from_attr]

        detail_records = []
        _logger.debug('Loop over supplierinfo children ...')

        adapter = self.unit_for(IntercompanyAdapter, model_name)

        detail_records = adapter.read(child_records,
                                      model_name='pricelist.partnerinfo')

        mapper = self._get_map_child_unit(model_name)

        items = mapper.get_items(
            detail_records, map_record, to_attr, options=self.options
        )

        _logger.debug('Product Supplierinfo: %s', items)

        return items

    @mapping
    def name(self, record):
        binder = self.binder_for('intercompany.res.partner')
        partner_id = binder.to_openerp(record['name'][0], unwrap=True)
        assert partner_id is not None, (
            "PartnerID should have been imported!"
        )
        return {'name': partner_id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def intercompany_id(self, record):
        return {'intercompany_id': record['id']}


@ic_odoo
class PricelistPartnerInfoImportMapper(ImportMapper):
    _model_name = ['pricelist.partnerinfo']

    direct = [('name', 'name'), ('min_quantity', 'min_quantity'),
              ('price', 'price')]

"""
E X P O R T
"""


@ic_odoo
class ProductSupplierinfoExportMapper(ExportMapper):
    _model_name = ['intercompany.product.supplierinfo']
    _map_child_class = IntercompanyExportMapChild

    direct = [('sequence', 'sequence'), ('product_name', 'product_name'),
              ('product_code', 'product_code'), ('min_qty', 'min_qty'),
              ('delay', 'delay')]

    children = [
        ('pricelist_ids', 'pricelist_ids', 'pricelist.partnerinfo')
    ]

    @mapping
    def name(self, record):
        binder = self.binder_for('intercompany.res.partner')
        partner_id = binder.to_backend(record.name.id, wrap=True)
        return {'name': partner_id}


@ic_odoo
class PricelistPartnerinfoExportMapper(ExportMapper):
    _model_name = ['pricelist.partnerinfo']

    direct = [('name', 'name'), ('min_quantity', 'min_quantity'),
              ('price', 'price')]
