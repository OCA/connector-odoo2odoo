# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping, ExportMapper)

from ..unit.import_synchronizer import (OdooImporter,
                                        DirectBatchImporter)
from ..unit.export_synchronizer import (OdooExporter)
from ..unit.mapper import OdooImportMapper
from ..backend import oc_odoo


_logger = logging.getLogger(__name__)


class OdooConnectorPartner(models.Model):
    _name = 'odooconnector.res.partner'
    _inherit = 'odooconnector.binding'
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'Odoo Connector Partner'

    openerp_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='restrict',
    )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.res.partner',
        inverse_name='openerp_id',
        string='Odoo Connector Binding'
    )


@oc_odoo
class PartnerBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.res.partner']


@oc_odoo
class PartnerImporter(OdooImporter):
    _model_name = ['odooconnector.res.partner']


@oc_odoo
class PartnerImportMapper(OdooImportMapper):
    _model_name = 'odooconnector.res.partner'

    direct = [('name', 'name'), ('is_company', 'is_company'),
              ('street', 'street'), ('street2', 'street2'), ('city', 'city'),
              ('zip', 'zip'), ('website', 'website'), ('phone', 'phone'),
              ('mobile', 'mobile'), ('fax', 'fax'), ('email', 'email'),
              ('comment', 'comment'), ('supplier', 'supplier'),
              ('customer', 'customer'), ('ref', 'ref'), ('lang', 'lang'),
              ('date', 'date'), ('notify_email', 'notify_email')]

    @mapping
    def country_id(self, record):

        if not record.get('country_id'):
            return
        country = self.env['res.country'].search(
            [('name', '=', record['country_id'][1])],
            limit=1
        )
        if country:
            return {'country_id': country.id}


@oc_odoo
class PartnerExporter(OdooExporter):
    _model_name = ['odooconnector.res.partner']

    def _get_remote_model(self):
        return 'res.partner'

    def _pre_export_check(self, record):
        if not self.backend_record.default_export_partner:
            return False

        domain = self.backend_record.default_export_partner_domain
        return self._pre_export_domain_check(record, domain)

    def _after_export(self, record_created):
        # create a ic_binding in the backend, indicating that the partner
        # was exported
        if record_created:
            record_id = self.binder.unwrap_binding(self.binding_id)
            data = {
                'backend_id': self.backend_record.export_backend_id,
                'openerp_id': self.external_id,
                'external_id': record_id,
                'exported_record': False
            }
            self.backend_adapter.create(
                data,
                model_name='odooconnector.res.partner',
                context={'connector_no_export': True}
            )


@oc_odoo
class PartnerExportMapper(ExportMapper):
    _model_name = 'odooconnector.res.partner'

    direct = [('name', 'name'), ('is_company', 'is_company'),
              ('street', 'street'), ('street2', 'street2'), ('city', 'city'),
              ('zip', 'zip'), ('website', 'website'), ('phone', 'phone'),
              ('mobile', 'mobile'), ('fax', 'fax'), ('email', 'email'),
              ('comment', 'comment'), ('supplier', 'supplier'),
              ('customer', 'customer'), ('ref', 'ref'), ('lang', 'lang'),
              ('date', 'date'), ('notify_email', 'notify_email')]
