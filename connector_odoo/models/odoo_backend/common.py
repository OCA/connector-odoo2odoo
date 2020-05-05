# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.addons.connector.models import checkpoint
from odoo.addons.connector_odoo.components.backend_adapter import (
    OdooAPI, OdooLocation)
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

# TODO : verify if needed
IMPORT_DELTA_BUFFER = 30  # seconds

_logger = logging.getLogger(__name__)


class OdooBackend(models.Model):
    """ Model for Odoo Backends """

    _name = "odoo.backend"
    _description = "Odoo Backend"
    _inherit = "connector.backend"

    _backend_type = "odoo"

    @api.model
    def _select_state(self):
        """Available States for this Backend"""
        return [
            ("draft", "Draft"),
            ("checked", "Checked"),
            ("production", "In Production"),
        ]

    @api.model
    def _select_versions(self):
        """ Available versions for this backend """
        return [("10.0", "Version 10.0.x"), ("12.0", "Version 12.0.x")]

    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        selection="_select_state", string="State", default="draft"
    )
    version = fields.Selection(
        selection="_select_versions", string="Version", required=True
    )
    login = fields.Char(
        string="Username / Login",
        required=True,
        help="Username in the external Odoo Backend.",
    )
    password = fields.Char(string="Password", required=True)
    database = fields.Char(string="Database", required=True)
    hostname = fields.Char(string="Hostname", required=True)
    port = fields.Integer(
        string="Port",
        required=True,
        help="For SSL, 443 is mostly the right choice",
        default=8069,
    )
    protocol = fields.Selection(
        selection=[("jsonrpc", "JsonRPC"), ("jsonrpc+ssl", "JsonRPC with SSL")],
        string="Protocol",
        required=True,
        default="jsonrpc",
        help="For SSL consider changing the port to 443",
    )
    default_lang_id = fields.Many2one(
        comodel_name="res.lang", string="Default Language"
    )
    export_backend_id = fields.Integer(
        string="Backend ID in the external system",
        help="""The backend id that represents this system in the external
                system.""",
    )

    export_partner_id = fields.Integer(
        string="Partner ID in the external System",
        help="""The partner id that represents this company in the
                external system.""",
    )

    default_export_backend = fields.Boolean(
        string="Default Export Backend",
        help="Use this backend as an automatic export target.",
    )

    """
    PARTNER SYNC OPTIONS
    """

    default_export_partner = fields.Boolean(string="Export Partners")
    default_import_partner = fields.Boolean(string="Import Partners")

    local_partner_domain_filter = fields.Char(
        string="Local Partners Domain", default="[]"
    )

    external_partner_domain_filter = fields.Char(
        string="External Partner domain filter",
        default="[]",
        help="""Filter in the Odoo Destination
        """,
    )

    matching_product_product = fields.Boolean(
        string="Match product", default=True
    )
    matching_product_ch = fields.Selection(
        [("default_code", "Reference"), ("barcode", "Barcode")],
        string="Matching Field for product",
        default="default_code",
        required=True,
    )
    matching_customer = fields.Boolean(
        string="Matching Customer",
        help="The selected fields will be matched to the ref field "
        "of the partner. Please adapt your datas consequently.",
        default=True,
    )
    matching_customer_ch = fields.Selection(
        [
            ("email", "Email"),
            ("barcode", "Barcode"),
            ("ref", "Internal reference"),
            ("vat", "TIN Number"),
        ],
        string="Matching Field for partner",
        default="ref",
    )
    local_product_domain_filter = fields.Char(
        string="Local Product domain filter",
        default="[]",
        help="Use this option per backend to specify which part of your "
        "catalog to synchronize",
    )
    external_product_domain_filter = fields.Char(
        string="External Product domain filter",
        default="[]",
        help="Filter in the Odoo Destination",
    )
    local_uom_uom_domain_filter = fields.Char(
        string="Local UOM domain filter",
        default="[]",
        help="Use this option per backend to specify which part of your "
        "catalog to synchronize",
    )
    external_uom_uom_domain_filter = fields.Char(
        string="External UOM domain filter",
        default="[]",
        help="Filter in the Odoo Destination",
    )
    external_product_pricelist_domain_filter = fields.Char(
        string="External Product Pricelist domain filter",
        default="[]",
        help="Filter in the Odoo Destination",
    )
    default_import_product = fields.Boolean("Import products")
    import_products_from_date = fields.Datetime("Import products from date")
    import_partner_from_date = fields.Datetime("Import partner from date")
    import_categories_from_date = fields.Datetime("Import categories from date")
    import_pricelist_items_from_date = fields.Datetime(
        "Import pricelists from date")
    default_export_product = fields.Boolean("Export Products")
    export_products_from_date = fields.Datetime("Export products from date")
    export_categories_from_date = fields.Datetime("Export Categories from date")
    default_category_id = fields.Integer(
        "Default Category ID",
        help="If set, this Id will be used instead of getting dependencies",
    )
    default_product_export_dict = fields.Char(
        "Default Json for creating/updating products",
        default="{'default_code': '/', 'active': False}",
    )
    pricelist_id = fields.Many2one(
        "product.pricelist", "Pricelist", required=True
    )

    @api.multi
    def get_default_language_code(self):
        lang = (
            self.default_lang_id.code
            or self.env.user.lang
            or self.env.context["lang"]
            or "en_US"
        )
        return lang

    @api.multi
    def _check_connection(self):
        self.ensure_one()
        odoo_location = OdooLocation(
            hostname=self.hostname,
            login=self.login,
            password=self.password,
            database=self.database,
            port=self.port,
            version=self.version,
            protocol=self.protocol,
            lang_id=self.get_default_language_code(),
        )
        odoo_api = OdooAPI(odoo_location)
        odoo_api.complete_check()
        self.write({"state": "checked"})

    @api.multi
    def button_check_connection(self):
        self._check_connection()

    @api.multi
    def button_reset_to_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        """
        Place the connexion here regarding the documentation
        http://odoo-connector.com/api/api_components.html\
            #odoo.addons.component.models.collection.Collection
        """
        self.ensure_one()
        lang = self.get_default_language_code()
        odoo_location = OdooLocation(
            hostname=self.hostname,
            login=self.login,
            password=self.password,
            database=self.database,
            port=self.port,
            version=self.version,
            protocol=self.protocol,
            lang_id=lang,
        )
        with OdooAPI(odoo_location) as odoo_api:
            _super = super(OdooBackend, self.with_context(lang=lang))
            # from the components we'll be able to do: self.work.odoo_api
            with _super.work_on(
                model_name, odoo_api=odoo_api, **kwargs
            ) as work:
                yield work

    @api.multi
    def synchronize_basedata(self):
        self.ensure_one()
        lang = self.get_default_language_code()
        self = self.with_context(lang=lang)
        try:
            for backend in self:
                for model_name in (
                    "odoo.uom.uom",
                    "odoo.product.attribute",
                    "odoo.product.attribute.value",
                ):
                    # import directly, do not delay because this
                    # is a fast operation, a direct return is fine
                    # and it is simpler to import them sequentially
                    self.env[model_name].with_context(lang=lang).import_batch(
                        backend, []
                    )
            return True
        except Exception as e:
            _logger.error(e, exc_info=True)
            raise UserError(
                _(
                    "Check your configuration, we can't get the data. "
                    "Here is the error:\n%s" % e
                )
            )

    @api.multi
    def add_checkpoint(self, record):
        self.ensure_one()
        record.ensure_one()
        return checkpoint.add_checkpoint(
            self.env, record._name, record.id, self._name, self.id
        )

    @api.multi
    def import_product_product(self):
        if not self.default_import_product:
            return False
        self._import_from_date(
            "odoo.product.product", "import_products_from_date"
        )
        return True

    @api.multi
    def import_product_template(self):
        if not self.default_import_product:
            return False
        self._import_from_date(
            "odoo.product.template", "import_products_from_date"
        )
        return True

    @api.multi
    def import_partner(self):
        if not self.default_import_partner:
            return False
        self._import_from_date("odoo.res.partner", "import_partner_from_date")
        return True

    @api.multi
    def import_product_pricelist_item(self):
        if not self.default_import_product:
            return False
        self._import_from_date(
            "odoo.product.pricelist.item", "import_pricelist_items_from_date"
        )
        return True

    @api.multi
    def import_product_categories(self):
        if not self.default_import_product:
            return False
        self._import_from_date(
            "odoo.product.category", "import_categories_from_date"
        )
        return True

    @api.multi
    def connector_client_synch(self, model, filters=[]):
        for backend in self:
            self.env[model].with_delay().import_batch(backend, filters)
        return True

    @api.multi
    def _import_from_date(self, model, from_date_field):
        import_start_time = datetime.now()
        filters = [
            ("write_date", "<", fields.Datetime.to_string(import_start_time))
        ]
        for backend in self:
            from_date = backend[from_date_field]
            if from_date:
                # from_date = fields.Datetime.from_string(from_date)
                filters.append(
                    (
                        "write_date",
                        ">",
                        import_start_time.strftime(
                            DEFAULT_SERVER_DATETIME_FORMAT
                        ),
                    )
                )
            else:
                from_date = None
            self.env[model].with_delay().import_batch(backend, filters)

        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({from_date_field: next_time})

    @api.multi
    def export_product_categories(self):
        if not self.default_export_product:
            return False
        self._export_from_date(
            "odoo.product.category", "export_categories_from_date"
        )
        return True

    @api.multi
    def export_product_products(self):
        if not self.default_export_product:
            return False
        self._export_from_date(
            "odoo.product.product", "export_products_from_date"
        )
        return True

    @api.multi
    def export_product_templates(self):
        if not self.default_export_product:
            return False
        self._export_from_date(
            "odoo.product.template", "export_products_from_date"
        )
        return True

    @api.multi
    def _export_from_date(self, model, from_date_field):
        self.ensure_one()
        import_start_time = datetime.now()
        filters = [
            ("write_date", "<", fields.Datetime.to_string(import_start_time))
        ]
        for backend in self:
            from_date = backend[from_date_field]
            if from_date:
                filters.append(("write_date", ">", from_date))
            else:
                from_date = None
            self.env[model].with_delay().export_batch(backend, filters)
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({from_date_field: next_time})
