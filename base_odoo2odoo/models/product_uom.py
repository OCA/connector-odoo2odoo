# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping, ImportMapper)
from ..unit.import_synchronizer import (IntercompanyImporter,
                                        DirectBatchImporter,
                                        TranslationImporter)
from ..backend import ic_odoo


_logger = logging.getLogger(__name__)


class IntercompanyProductUom(models.Model):
    _name = 'intercompany.product.uom'
    _inherit = 'intercompany.binding'
    _inherits = {'product.uom': 'openerp_id'}
    _description = 'Intercompany Product UoM'

    openerp_id = fields.Many2one(
        comodel_name='product.uom',
        string='Product UoM',
        required=True,
        ondelete='restrict'
    )


class ProductUom(models.Model):
    _inherit = 'product.uom'

    ic_bind_ids = fields.One2many(
        comodel_name='intercompany.product.uom',
        inverse_name='openerp_id',
        string='Intercompany Bindings'
    )


@ic_odoo
class ProductUomBatchImporter(DirectBatchImporter):
    _model_name = ['intercompany.product.uom']
    _ic_model_name = 'product.uom'


@ic_odoo
class ProductUomTranslationImporter(TranslationImporter):
    _model_name = ['intercompany.product.uom']
    _ic_model_name = 'product.uom'


@ic_odoo
class ProductUomImportMapper(ImportMapper):
    _model_name = ['intercompany.product.uom']

    direct = [('name', 'name'), ('active', 'active'),
              ('uom_type', 'uom_type'), ('factor', 'factor'),
              ('rounding', 'rounding'), ]

    @mapping
    def category_id(self, record):
        if not record.get('category_id'):
            return

        print record.get('category_id')
        uom_categ = self.env['product.uom.categ']
        search = [('name', '=', record['category_id'][1])]
        for l in ['de_DE', 'en_US']:  # TODO: Better fix that!
            res = uom_categ.with_context(lang=l).search(search, limit=1)
            if res:
                return {'category_id': res.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@ic_odoo
class ProductUomSimpleImportMapper(ImportMapper):
    _model_name = ['intercompany.product.uom']

    direct = [('name', 'name')]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@ic_odoo
class ProductUomImporter(IntercompanyImporter):
    _model_name = ['intercompany.product.uom']
    _ic_model_name = 'product.uom'
    _base_mapper = ProductUomImportMapper

    def _create(self, data):
        """Check first if we find the UoM by name"""
        search = [('name', '=', data['name'])]
        for l in ['de_DE', 'en_US']:
            res = self.env['product.uom'].with_context(lang=l).search(search)
            if res:
                _data = {'backend_id': data['backend_id'],
                         'openerp_id': res.id}
                binding = super(ProductUomImporter, self)._create(_data)
                return binding
        return super(ProductUomImporter, self)._create(data)

    def _after_import(self, binding):
        _logger.debug('Product UoM Importer: _after_import called')
        translation_importer = self.unit_for(TranslationImporter)
        translation_importer.run(
            self.intercompany_id,
            binding.id,
            mapper_class=ProductUomSimpleImportMapper
        )
