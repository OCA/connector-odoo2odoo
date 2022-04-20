import logging

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class AccountAccountBatchImporter(Component):
    """Import the Odoo Account Account.

    For every Account Account in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.account.account.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.account"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo Account Account %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountAccountImportMapper(Component):
    _name = "odoo.account.account.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.account.account"]

    direct = [
        ("code", "code"),
        ("name", "name"),
        ("reconcile", "reconcile"),
        ("note", "note"),
    ]

    @only_create
    @mapping
    def check_account_account_exists(self, record):
        res = {}

        account_id = self.env["account.account"].search([("code", "=", record.code)])
        _logger.debug("Account Account found for %s : %s" % (record, account_id))
        if len(account_id) == 1:
            res.update({"odoo_id": account_id.id})
        return res

    @mapping
    def currency_id(self, record):
        return {"currency_id": self.work.origing_account_id.currency_id.id}

    @mapping
    def deprecated(self, record):
        return {"deprecated": self.work.origing_account_id.deprecated}

    @mapping
    def user_type_id(self, record):
        return {"user_type_id": self.work.origing_account_id.user_type_id.id}

    @mapping
    def tax_ids(self, record):
        return {"tax_ids": [(6, 0, self.work.origing_account_id.tax_ids.ids)]}

    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}

    @mapping
    def tag_ids(self, record):
        return {"tag_ids": [(6, 0, self.work.origing_account_id.tag_ids.ids)]}

    @mapping
    def group_id(self, record):
        return {"group_id": self.work.origing_account_id.group_id.id}

    @mapping
    def root_id(self, record):
        return {"root_id": self.work.origing_account_id.root_id.id}

    @mapping
    def allowed_journal_ids(self, record):
        return {
            "allowed_journal_ids": [
                (6, 0, self.work.origing_account_id.allowed_journal_ids.ids)
            ]
        }


class AccountAccountImporter(Component):
    _name = "odoo.account.account.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.account"]

    def _must_skip(
        self,
    ):
        return self.env["account.account"].search(
            [("code", "=", self.odoo_record.code)]
        )

    def _before_import(
        self,
    ):
        account_id = self.env["account.account"].search(
            [("code", "=", self.odoo_record.code)]
        )
        if not account_id:
            account_lenght = self.env.user.company_id.chart_template_id.code_digits
            account_code = self.odoo_record.code[:3]
            origing_account_id = self.env["account.account"].search(
                [("code", "=", account_code + ("0" * (account_lenght - 3)))]
            )
            if not origing_account_id:
                raise ValidationError(
                    _("Account Origin %s not found") % self.odoo_record.code
                )
            else:
                self.work.origing_account_id = origing_account_id
