# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class UserBatchImporter(Component):
    """Import the Odoo User.

    For every user in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.res.users.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.res.users"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo user %s returned %s items", filters, len(external_ids)
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options)


class UserImportMapper(Component):
    _name = "odoo.res.users.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.res.users"]

    # TODO: groups and other fields (we recommend to use server-backend/base_user_role)
    direct = [
        ("name", "name"),
        ("login", "login"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        filters = ast.literal_eval(self.backend_record.local_user_domain_filter)
        if record.login or record.name:
            filters.extend(
                [
                    "|",
                    ("login", "=", record.login),
                    ("name", "=", record.name),
                ]
            )
        user = self.env["res.users"].search(filters)
        if len(user) == 1:
            return {"odoo_id": user.id}
        return {}

    # @mapping
    # def image(self, record):
    #     if (self.backend_record.version in (
    #         '6.1', '7.0', '8.0', '9.0', '10.0', '11.0', '12.0')):
    #         return {"image_1920": record.image if hasattr(record, 'image') else False}
    #     else:
    #         return {"image_1920": record.image_1920}


class UserImporter(Component):
    _name = "odoo.res.user.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.res.users"]
