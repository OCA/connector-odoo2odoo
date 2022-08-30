import logging

from odoo import fields, models

from odoo.addons.component.core import Component
from odoo.addons.component_event.components.event import skip_if

_logger = logging.getLogger(__name__)


class OdooIrAttachment(models.Model):
    _name = "odoo.ir.attachment"
    _inherit = "odoo.binding"
    _inherits = {"ir.attachment": "odoo_id"}
    _description = "External Odoo Attachment"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        if self.backend_id.partner_main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    bind_ids = fields.One2many(
        comodel_name="odoo.ir.attachment",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class IrAttachmentAdapter(Component):
    _name = "odoo.ir.attachment.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.ir.attachment"

    _odoo_model = "ir.attachment"


class IrAttachmentListener(Component):
    _name = "ir.attachment.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["ir.attachment"]
    _usage = "event.listener"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        # FIXME: do the proper way
        bind_model = self.env["odoo.ir.attachment"]
        backend = self.env["odoo.backend"].search([])
        if backend:
            binding = bind_model.create(
                {
                    "backend_id": backend[0].id,
                    "odoo_id": record.id,
                    "external_id": 0,
                }
            )
            binding.with_delay().export_record(backend)
        else:
            _logger.info("No backend found for attachment %s", record.id)
