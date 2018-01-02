# -*- coding: utf-8 -*-
# © 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector.connector import Binder

from ..backend import odoo
from ..connector import create_binding


class OdooBinder(Binder):
    """Generic Binder for a Odoo backend."""


@odoo
class OdooModelBinder(OdooBinder):
    """
    Bindings are done directly on the binding model.

    Binding models are models called ``odoo.{normal_model}``,
    like ``odoo.res.partner`` or ``odoo.product.product``.
    They are ``_inherits`` of the normal models and contains
    the external Odoo ID, the ID of the Odoo backend and the additional
    fields belonging to the Odoo instance.
    """
    _model_name = []
    _external_field = 'external_odoo_id'
    _backend_field = 'backend_id'
    _openerp_field = 'odoo_id'
    _sync_date_field = 'sync_date'

    def _search_record(self, external_id, record_data):
        """May be overridden by subclasses to search a valid record
        to bind with the external one.
        """
        model_name = self.model.fields_get(
            [self._openerp_field])[self._openerp_field]['relation']
        return self.env[model_name].browse()

    def to_openerp(self, external_id, unwrap=False, record_data=None):
        """Overload the standard `connector.Binder` method to add an extra
        parameter `record_data` helping to match an existing record with the
        external one with other criteria than the external ID.
        If an existing record is found (and not bound yet), it will be bound
        to the external ID.
        """
        # Standard binding resolution
        binding = super(OdooModelBinder, self).to_openerp(
            external_id, unwrap=unwrap)
        # If no binding has been found, try to match an existing record thanks
        # to the external record data
        if not binding and record_data:
            record = self._search_record(external_id, record_data)
            if record:
                record.ensure_one()
                binding = self.model.search(
                    [('odoo_id', '=', record.id),
                     ('backend_id', '=', self.backend_record)])
                if not binding:
                    binding = create_binding(
                        self.session,
                        record._name, record.id,
                        self.backend_record.id)
                # Bind the local record with its external ID
                if not binding.external_odoo_id:
                    self.bind(external_id, binding.id)
                if unwrap:
                    binding = getattr(binding, self._openerp_field)
                return binding
        return binding
