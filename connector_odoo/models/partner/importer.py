# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


def get_state_from_record(self, record):
    state_id = False
    country_id = False
    if record.country_id:
        country_code = record.country_id.code
    else:
        country_code = "CA"
    country = self.env["res.country"].search(
        [
            ("code", "=", country_code),
        ]
    )
    country_id = country.id
    if hasattr(record, "state_id") and record.state_id:
        state = self.env["res.country.state"].search(
            [
                ("code", "=", record.state_id.code),
                ("country_id", "=", country_id),
            ]
        )
        if not state:
            state = self.env["res.country.state"].search(
                [
                    ("name", "=", record.state_id.name),
                    ("country_id", "=", country_id),
                ]
            )
        state_id = state.id
    return {
        "state_id": state_id,
        "country_id": country_id,
    }


class PartnerBatchImporter(Component):
    """Import the Odoo Partner.

    For every partner in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.res.partner.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.res.partner"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo partner %s returned %s items", filters, len(external_ids)
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options)


class PartnerImportMapper(Component):
    _name = "odoo.res.partner.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.res.partner"]

    # TODO :     special_price => minimal_price
    direct = [
        ("name", "name"),
        ("website", "website"),
        ("lang", "lang"),
        ("ref", "ref"),
        ("comment", "comment"),
        ("company_type", "company_type"),
        ("zip", "zip"),
        ("delivery_margin", "delivery_margin"),
    ]

    @mapping
    def category_id(self, record):
        if record.category_id:
            binder = self.binder_for("odoo.res.partner.category")
            return {
                "category_id": [
                    (
                        6,
                        0,
                        [
                            binder.to_internal(category_id, unwrap=True).id
                            for category_id in record.category_id.ids
                        ],
                    )
                ]
            }

    @mapping
    def street(self, record):
        # res.partner.address imported as dependency
        # in other version of odoo, this field is a direct mapping
        if self.backend_record.version != "6.1":
            return {"street": record.street}

    @mapping
    def street2(self, record):
        # res.partner.address imported as dependency
        # in other version of odoo, this field is a direct mapping
        if self.backend_record.version != "6.1":
            return {"street2": record.street2}

    @mapping
    def phone(self, record):
        # res.partner.address imported as dependency
        # in other version of odoo, this field is a direct mapping
        if self.backend_record.version != "6.1":
            return {"phone": record.phone}

    @mapping
    def mobile(self, record):
        # res.partner.address imported as dependency
        # in other version of odoo, this field is a direct mapping
        if self.backend_record.version != "6.1":
            return {"mobile": record.mobile}

    @mapping
    def city(self, record):
        # res.partner.address imported as dependency
        # in other version of odoo, this field is a direct mapping
        if self.backend_record.version != "6.1":
            return {"city": record.city}

    @mapping
    def state_id(self, record):
        # res.partner.address imported as dependency
        # in other version of odoo, this field is a direct mapping
        if self.backend_record.version != "6.1":
            return get_state_from_record(self, record)

    @mapping
    def customer(self, record):
        if self.backend_record.version in (
            "6.1",
            "7.0",
            "8.0",
            "9.0",
            "10.0",
            "11.0",
            "12.0",
        ):
            return {"customer_rank": record.customer}
        else:
            return {"customer_rank": record.customer_rank}

    @mapping
    def supplier(self, record):
        if self.backend_record.version in (
            "6.1",
            "7.0",
            "8.0",
            "9.0",
            "10.0",
            "11.0",
            "12.0",
        ):
            return {"supplier_rank": record.supplier}
        else:
            return {"supplier_rank": record.supplier_rank}

    @mapping
    def image(self, record):
        if self.backend_record.version in (
            "6.1",
            "7.0",
            "8.0",
            "9.0",
            "10.0",
            "11.0",
            "12.0",
        ):
            return {"image_1920": record.image if hasattr(record, "image") else False}
        else:
            return {"image_1920": record.image_1920}

    @mapping
    def user_id(self, record):
        if record.user_id:
            binder = self.binder_for("odoo.res.users")
            user = binder.to_internal(record.user_id.id, unwrap=True)
            return {"user_id": user.id}

    @mapping
    def property_account_payable(self, record):
        if float(self.backend_record.version) >= 9.0:
            property_account_payable_id = record.property_account_payable_id
        else:
            property_account_payable_id = record.property_account_payable

        if property_account_payable_id:
            binder = self.binder_for("odoo.account.account")
            account = binder.to_internal(property_account_payable_id.id, unwrap=True)
            if account:
                return {"property_account_payable_id": account.id}

    @mapping
    def property_account_receivable(self, record):
        if float(self.backend_record.version) >= 9.0:
            property_account_receivable_id = record.property_account_receivable_id
        else:
            property_account_receivable_id = record.property_account_receivable

        if property_account_receivable_id:
            binder = self.binder_for("odoo.account.account")
            account = binder.to_internal(property_account_receivable_id.id, unwrap=True)
            if account:
                return {"property_account_receivable_id": account.id}

    @mapping
    def property_purchase_currency_id(self, record):
        property_purchase_currency_id = None
        if hasattr(record, "property_purchase_currency_id"):
            property_purchase_currency_id = record.property_purchase_currency_id
        if not property_purchase_currency_id:
            if (
                record.property_product_pricelist_purchase
                and record.property_product_pricelist_purchase.currency_id
            ):
                property_purchase_currency_id = (
                    record.property_product_pricelist_purchase.currency_id
                )
        if property_purchase_currency_id:
            binder = self.binder_for("odoo.res.currency")
            currency = binder.to_internal(property_purchase_currency_id.id, unwrap=True)
            if currency:
                return {"property_purchase_currency_id": currency.id}


class PartnerImporter(Component):
    _name = "odoo.res.partner.importer"
    _inherit = "odoo.importer"
    _inherits = "AbstractModel"
    _apply_on = ["odoo.res.partner"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        # import parent
        _logger.info("Importing dependencies for external ID %s", self.external_id)
        if self.odoo_record.parent_id:
            _logger.info("Importing parent")
            self._import_dependency(
                self.odoo_record.parent_id.id, "odoo.res.partner", force=force
            )

        if self.odoo_record.user_id:
            _logger.info("Importing user")
            self._import_dependency(
                self.odoo_record.user_id.id, "odoo.res.users", force=force
            )

        _logger.info("Importing categories")
        for category_id in self.odoo_record.category_id:
            self._import_dependency(
                category_id.id, "odoo.res.partner.category", force=force
            )

        if self.odoo_record.property_account_payable:
            _logger.info("Importing account payable")
            self._import_dependency(
                self.odoo_record.property_account_payable.id,
                "odoo.account.account",
                force=force,
            )

        if self.odoo_record.property_account_receivable:
            _logger.info("Importing account receivable")
            self._import_dependency(
                self.odoo_record.property_account_receivable.id,
                "odoo.account.account",
                force=force,
            )

        if (
            hasattr(self.odoo_record, "property_purchase_currency_id")
            and self.odoo_record.property_purchase_currency_id
        ):
            _logger.info("Importing supplier currency")
            self._import_dependency(
                self.odoo_record.property_purchase_currency_id.id,
                "odoo.res.currency",
                force=force,
            )

        if (
            self.odoo_record.property_product_pricelist_purchase
            and self.odoo_record.property_product_pricelist_purchase.currency_id
        ):
            _logger.info("Importing supplier currency")
            self._import_dependency(
                self.odoo_record.property_product_pricelist_purchase.currency_id.id,
                "odoo.res.currency",
                force=force,
            )

        result = super()._import_dependencies(force=force)
        _logger.info("Dependencies imported for external ID %s", self.external_id)
        return result

    def _after_import(self, binding, force=False):
        if self.backend_record.version == "6.1":
            _logger.info(
                "OpenERP detected, importing adresses for external ID %s",
                self.external_id,
            )
            self.env["odoo.res.partner.address.disappeared"].with_delay().import_record(
                self.backend_record, self.external_id
            )
        return super()._after_import(binding, force)
