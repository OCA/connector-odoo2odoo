# -*- coding: utf-8 -*-
# © 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.addons.connector.queue.job import job

from ..connector import get_environment

_logger = logging.getLogger(__name__)


class OdooExporter(Exporter):
    _model_name = []
    _raw_mode = False   # TODO does nothing currently, feature to implement

    def run(self, binding_id):
        """Run the synchronization (create or update the external Odoo record).
        Returns `True` if the record has been exported.
        """
        binding = self.model.browse(binding_id)
        if not self.check_export(binding):
            _logger.info(
                u"%s - Skipping export for binding record '%s'",
                binding.backend_id.name, binding)
            return
        if binding.external_odoo_id:
            self.update_document(binding)
        else:
            self.create_document(binding)
        return True

    def check_export(self, binding):
        """Check if the binding record should be exported."""
        return True

    def update_document(self, binding):
        mapped_record = self.mapper.map_record(binding)
        data = mapped_record.values()
        return self.backend_adapter.write([binding.external_odoo_id], data)

    def create_document(self, binding):
        mapped_record = self.mapper.map_record(binding)
        data = mapped_record.values(for_create=True)
        external_id = self.backend_adapter.create(data)
        self.binder.bind(external_id, binding.id)
        return external_id


@job(default_channel='root.o2o')
def export_binding(session, model_name, binding_id):
    """Export a binding record on Odoo."""
    binding = session.env[model_name].browse(binding_id)
    backend_id = binding.backend_id.id
    env = get_environment(session, model_name, backend_id)
    exporter = env.get_connector_unit(OdooExporter)
    _logger.info(
        u"%s - Exporting binding record '%s'...",
        binding.backend_id.name, binding)
    exporter.run(binding_id)


# Deprecated, kept for backward compatibility.
export_record = export_binding
