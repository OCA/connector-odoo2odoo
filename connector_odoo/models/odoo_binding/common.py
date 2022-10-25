# -*- coding: utf-8 -*-
# © 2013-2017 Guewen Baconnier,Camptocamp SA,Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action


class OdooBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All the models used as bindings between Magento and Odoo
    (``magento.res.partner``, ``magento.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'odoo.binding'
    _inherit = 'external.binding'
    _description = 'Odoo Binding (abstract)'

    # odoo_id = odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='odoo.backend',
        string='Odoo Backend',
        required=True,
        ondelete='restrict',
    )
    # fields.Char because 0 is a valid Magento ID
    external_id = fields.Char(string='ID on Ext Odoo')

    _sql_constraints = [
        ('odoo_uniq', 'unique(backend_id, external_id)',
         'A binding already exists with the same Odoo ID.'),
    ]

    @job(default_channel='root.odoo')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on Odoo """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.odoo')
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a Odoo record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)

    @job(default_channel='root.odoo')
    @api.multi
    def export_record(self, fields=None):
        """ Export a record on Odoo """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

    @job(default_channel='root.odoo')
    @api.multi
    def export_delete_record(self, backend, external_id):
        """ Delete a record on Odoo """
        with backend.work_on(self._name) as work:
            deleter = work.component(usage='record.exporter.deleter')
            return deleter.run(external_id)
