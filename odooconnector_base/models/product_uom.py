# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping)
from ..unit.import_synchronizer import (OdooImporter,
                                        DirectBatchImporter,
                                        TranslationImporter)
from ..unit.mapper import (OdooImportMapper)
from ..backend import oc_odoo


_logger = logging.getLogger(__name__)


class OdooConnectorProductUom(models.Model):
    _name = 'odooconnector.product.uom'
    _inherit = 'odooconnector.binding'
    _inherits = {'product.uom': 'openerp_id'}
    _description = 'Odoo Connector Product UoM'

    openerp_id = fields.Many2one(
        comodel_name='product.uom',
        string='Product UoM',
        required=True,
        ondelete='restrict'
    )


class ProductUom(models.Model):
    _inherit = 'product.uom'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.product.uom',
        inverse_name='openerp_id',
        string='Odoo Bindings'
    )


@oc_odoo
class ProductUomBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.product.uom']
    _ic_model_name = 'product.uom'


@oc_odoo
class ProductUomTranslationImporter(TranslationImporter):
    _model_name = ['odooconnector.product.uom']
    _ic_model_name = 'product.uom'


@oc_odoo
class ProductUomImportMapper(OdooImportMapper):
    _model_name = ['odooconnector.product.uom']

    direct = [('name', 'name'), ('active', 'active'),
              ('uom_type', 'uom_type'), ('factor', 'factor'),
              ('rounding', 'rounding'), ]

    @mapping
    def category_id(self, record):
        if not record.get('category_id'):
            return

        uom_categ = self.env['product.uom.categ']
        search = [('name', '=', record['category_id'][1])]
        for l in ['de_DE', 'en_US']:  # TODO: Better fix that!
            res = uom_categ.with_context(lang=l).search(search, limit=1)
            if res:
                return {'category_id': res.id}


@oc_odoo
class ProductUomSimpleImportMapper(OdooImportMapper):
    _model_name = ['odooconnector.product.uom']

    direct = [('name', 'name')]


@oc_odoo
class ProductUomImporter(OdooImporter):
    _model_name = ['odooconnector.product.uom']
    _ic_model_name = 'product.uom'
    _base_mapper = ProductUomImportMapper

    def _create(self, data):
        # Check first if we find the UoM by name
        search = [('name', '=', data['name'])]
        for l in ['de_DE', 'en_US']:
            res = self.env['product.uom'].with_context(lang=l).search(search)
            if res:
                _data = {'backend_id': data['backend_id'],
                         'openerp_id': res.id}
                binding = super(ProductUomImporter, self)._create(_data)
                return binding

        # TODO: Make the creation of product.uom depend on a flag in the
        #       backend record which determines if it should be created or not
        return super(ProductUomImporter, self)._create(data)

    def _after_import(self, binding):
        _logger.debug('Product UoM Importer: _after_import called')
        translation_importer = self.unit_for(TranslationImporter)
        translation_importer.run(
            self.external_id,
            binding.id,
            mapper_class=ProductUomSimpleImportMapper
        )
