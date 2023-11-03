# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooUser(models.Model):
    _name = "odoo.res.users"
    _inherit = "odoo.binding"
    _inherits = {"res.users": "odoo_id"}
    _description = "External Odoo User"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def name_get(self):
        result = []
        for op in self:
            name = "{} (Backend: {})".format(
                op.odoo_id.display_name, op.backend_id.display_name
            )
            result.append((op.id, name))

        return result

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class User(models.Model):
    _inherit = "res.users"

    bind_ids = fields.One2many(
        comodel_name="odoo.res.users",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class UserAdapter(Component):
    _name = "odoo.res.users.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.res.users"

    _odoo_model = "res.users"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        """Search records according to some criteria
        and returns a list of ids

        :rtype: list
        """
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_user_domain_filter)
        )
        filters += ext_filter or []
        return super(UserAdapter, self).search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class UserListener(Component):
    _name = "res.users.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["res.users"]
    _usage = "event.listener"
