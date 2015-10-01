# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping, ImportMapper,
                                                  ExportMapper)
from ..unit.import_synchronizer import (IntercompanyImporter,
                                        DirectBatchImporter,
                                        TranslationImporter)
from ..unit.export_synchronizer import (IntercompanyExporter,
                                        TranslationExporter)
from ..unit.mapper import (IntercompanyImportMapChild,
                           IntercompanyExportMapChild)
from ..unit.backend_adapter import IntercompanyAdapter
from ..backend import ic_odoo


_logger = logging.getLogger(__name__)


class IntercompanyProductTemplate(models.Model):
    _name = 'intercompany.product.product'
    _inherit = 'intercompany.binding'
    _inherits = {'product.product': 'openerp_id'}
    _description = 'Intercompany Product'

    openerp_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='restrict'
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    ic_bind_ids = fields.One2many(
        comodel_name='intercompany.product.product',
        inverse_name='openerp_id',
        string='Intercompany Bindings'
    )


@ic_odoo
class ProductBatchImporter(DirectBatchImporter):
    _model_name = ['intercompany.product.product']


@ic_odoo
class ProductTranslationImporter(TranslationImporter):
    _model_name = ['intercompany.product.product']


@ic_odoo
class ProductImportMapper(ImportMapper):
    _model_name = ['intercompany.product.product']
    _map_child_class = IntercompanyImportMapChild

    direct = [('name', 'name'), ('name_template', 'name_template'),
              ('type', 'type'),
              ('purchase_ok', 'purchase_ok'), ('sale_ok', 'sale_ok'),
              ('lst_price', 'lst_price'), ('standard_price', 'standard_price'),
              ('ean13', 'ean13'), ('default_code', 'default_code'),
              ('description', 'description')]

    children = [
        ('seller_ids', 'seller_ids', 'intercompany.product.supplierinfo'),
    ]

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        source = map_record.source
        child_records = source[from_attr]

        detail_records = []
        _logger.debug('Loop over product children ...')
        for child_record in child_records:
            adapter = self.unit_for(IntercompanyAdapter,
                                    model_name)

            detail_record = adapter.read(child_record)
            detail_records.append(detail_record)

        mapper = self._get_map_child_unit(model_name)

        items = mapper.get_items(
            detail_records, map_record, to_attr, options=self.options
        )
        # children.extend(items)

        _logger.debug('Product child "%s": %s', model_name, items)

        return items

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def uom_id(self, record):

        if not record.get('uom_id'):
            return

        uom = self.env['product.uom'].search(
            [('name', '=', record['uom_id'][1])],
            limit=1
        )

        if uom:
            return {'uom_id': uom.id}

    @mapping
    def uom_po_id(self, record):

        if not record.get('uom_id'):
            return

        uom = self.env['product.uom'].search(
            [('name', '=', record['uom_po_id'][1])],
            limit=1
        )

        if uom:
            return {'uom_po_id': uom.id}


@ic_odoo
class ProductSimpleImportMapper(ImportMapper):
    _model_name = ['intercompany.product.product']

    direct = [('name', 'name'), ('name_template', 'name_template'),
              ('description', 'description')]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@ic_odoo
class ProductImporter(IntercompanyImporter):
    _model_name = ['intercompany.product.product']

    # We have to set a explicit mapper since there are two different
    # mappers that might match
    _base_mapper = ProductImportMapper

    def _after_import(self, binding):
        _logger.debug('Product Importer: _after_import called')
        translation_importer = self.unit_for(TranslationImporter)
        translation_importer.run(
            self.intercompany_id,
            binding.id,
            mapper_class=ProductSimpleImportMapper
        )

    def _is_uptodate(self, binding):
        res = super(ProductImporter, self)._is_uptodate(binding)

        if res:
            _logger.debug('Check also the last product.template write date...')
            product_tmpl_id = self.intercompany_record['product_tmpl_id'][0]
            product_tmpl = self.backend_adapter.read(
                product_tmpl_id, model_name='product.template')
            if product_tmpl:
                date_from_string = fields.Datetime.from_string
                sync_date = date_from_string(binding.sync_date)
                intercompany_date = date_from_string(product_tmpl[
                                                     'write_date'])

                return intercompany_date < sync_date

        return res


@ic_odoo
class ProductImportChildMapper(IntercompanyImportMapChild):
    _model_name = ['intercompany.product.supplierinfo']


"""
E X P O R T

Classes related to exporting data
"""


@ic_odoo
class ProductExportMapper(ExportMapper):
    _model_name = ['intercompany.product.product']
    _map_child_class = IntercompanyExportMapChild

    direct = [('name', 'name'), ('name_template', 'name_template'),
              ('type', 'type'),
              ('purchase_ok', 'purchase_ok'), ('sale_ok', 'sale_ok'),
              ('lst_price', 'lst_price'), ('standard_price', 'standard_price'),
              ('ean13', 'ean13'), ('default_code', 'default_code'),
              ('description', 'description')]

    children = [
        ('seller_ids', 'seller_ids', 'intercompany.product.supplierinfo')
    ]

    @mapping
    def uom_id(self, record):
        print record
        if not record.uom_id.id:
            return
        # TODO: Unnecessary round trip ...
        adapter = self.unit_for(IntercompanyAdapter, 'product.uom')
        filters = [('name', '=', record.uom_id.name), ]
        uom = adapter.search(
            filters=filters,
            context={'lang': 'en_US'},  # TODO: In general better lang support!
            model_name='product.uom')

        if uom and len(uom) == 1:
            return {'uom_id': uom[0]}


@ic_odoo
class ProductTranslationExporter(TranslationExporter):
    _model_name = ['intercompany.product.product']


# TODO(MJ): Instead of definining a specific translation mapper for each model
#           a special translation mapper should be used that create the list
#           of direct fields dynamically based on a given list of fields,
#           e.g. the list of translatable fields.
@ic_odoo
class ProductTranslationExportMapper(ExportMapper):
    _model_name = ['intercompany.product.product']
    direct = [('name', 'name'), ('name_template', 'name_template'),
              ('description', 'description')]


@ic_odoo
class ProductExporter(IntercompanyExporter):
    _model_name = ['intercompany.product.product']
    _base_mapper = ProductExportMapper

    def _pre_export_check(self, record):
        """ Run some checks before exporting the record """
        if not self.backend_record.default_export_product:
            return False

        domain = self.backend_record.default_export_product_domain
        return self._pre_export_domain_check(record, domain)

    def _after_export(self, record_created):
        _logger.debug('Product exporter: _after_export called')
        translations_exporter = self.unit_for(TranslationExporter)
        translations_exporter.run(
            self.intercompany_id,
            self.binding_id,
            mapper_class=ProductTranslationExportMapper)

        if record_created:
            record_id = self.binder.unwrap_binding(self.binding_id)
            data = {
                'backend_id': self.backend_record.export_backend_id,
                'openerp_id': self.intercompany_id,
                'intercompany_id': record_id,
                'exported_record': False
            }
            self.backend_adapter.create(
                data,
                model_name='intercompany.product.product',
                context={'connector_no_export': True}
            )
