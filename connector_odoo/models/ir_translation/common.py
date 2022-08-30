import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooIrTranslation(models.Model):
    _name = "odoo.ir.translation"
    _inherit = "odoo.binding"
    _inherits = {"ir.translation": "odoo_id"}
    _description = "External Odoo Translation"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def write(self, vals):
        # Saving data in binder (odoo.ir.translation) not change res_id in ir.translation
        # So we need to update res_id in ir.translation
        # This happend when delete record with translation in odoo and reimport it
        if "res_id" in vals:
            self.odoo_id.res_id = vals["res_id"]
        return super().write(vals)

    def resync(self):
        if self.backend_id.partner_main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class IrTranslation(models.Model):
    _inherit = "ir.translation"

    bind_ids = fields.One2many(
        comodel_name="odoo.ir.translation",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class IrTranslationAdapter(Component):
    _name = "odoo.ir.translation.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.ir.translation"

    _odoo_model = "ir.translation"

    def _update(self, binding, data):
        """Update an Odoo record"""
        # special check on data before import
        self._validate_data(data)
        binding.odoo_id.write(data)
        binding.with_context(connector_no_export=True).write(data)
        return


class IrTranslationListener(Component):
    _name = "ir.translation.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["ir.translation"]
    _usage = "event.listener"
