# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

# pylint: disable=W7950
from odoo.addons.connector_odoo.models.partner.importer import get_state_from_record

_logger = logging.getLogger(__name__)


class OdooResPartnerAddressReferences(models.Model):
    _name = "odoo.res.partner.address.disappeared"
    _inherit = "odoo.binding"
    _inherits = {"res.partner": "odoo_id"}

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    odoo_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", ondelete="cascade"
    )

    odoo_binding_partner_id = fields.Many2one("odoo.res.partner")
    external_parent_partner_id = fields.Integer()

    def resync(self):
        if self.backend_id.main_record == "odoo":
            raise NotImplementedError
        else:
            return self.with_delay().import_address(
                self.backend_id,
                self.external_id,
                self.external_parent_partner_id,
                force=True,
            )

    def default_address_contact_values(self, address, main_partner=False):
        state_country = get_state_from_record(self, address)
        result = {
            "type": address.type if address.type != "default" else "contact",
            "street": address.street,
            "street2": address.street2,
            "phone": address.phone,
            "mobile": address.mobile,
            "city": address.city,
            "zip": address.zip,
            "email": address.email,
            "name": address.name if address.name else main_partner.name,
        }
        result = {**state_country, **result}
        if main_partner:
            result["parent_id"] = main_partner.id
        return result

    def import_address(self, backend_record, address_id, partner_external_id):
        _logger.info("Obtaining address {}".format(address_id))
        address_model = backend_record.get_connection().api.get("res.partner.address")
        main_partner = (
            self.env["odoo.res.partner"]
            .search([("external_id", "=", partner_external_id)])
            .odoo_id
        )
        address = address_model.browse(address_id)
        payload = self.default_address_contact_values(address, main_partner)
        disappeared_link_id = self.env["odoo.res.partner.address.disappeared"].search(
            [("external_id", "=", address_id)]
        )
        if disappeared_link_id:
            disappeared_link_id.odoo_id.write(payload)
        else:
            if not payload["name"]:
                payload["name"] = self.odoo_record.name
            payload = {
                **payload,
                **{
                    "backend_id": backend_record.id,
                    "external_id": address_id,
                    "external_parent_partner_id": partner_external_id,
                },
            }
            self.env["odoo.res.partner.address.disappeared"].with_context(
                connector_no_export=True
            ).create(payload)
        self.after_import_address(
            backend_record, address_id, partner_external_id, address
        )

    def after_import_address(
        self, backend_record, address_id, partner_external_id, address
    ):
        pass


class PartnerAddressDissapearedAdapter(Component):
    _name = "odoo.res.partner.addresss.dissapeared.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.res.partner.address.disappeared"

    _odoo_model = "res.partner"


class Partner(models.Model):
    _inherit = "res.partner"

    bind_address_dissapeared_ids = fields.One2many(
        comodel_name="odoo.res.partner.address.disappeared",
        inverse_name="odoo_id",
        string="Odoo Address (Disappeared) Bindings",
    )
