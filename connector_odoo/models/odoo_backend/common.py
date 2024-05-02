# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# pylint: disable=W7950
from odoo.addons.connector_odoo.components.backend_adapter import OdooAPI, OdooLocation

# TODO : verify if needed
IMPORT_DELTA_BUFFER = 30  # seconds

_logger = logging.getLogger(__name__)


class OdooBackend(models.Model):
    """Model for Odoo Backends"""

    _name = "odoo.backend"
    _description = "Odoo Backend"
    _inherit = "connector.backend"

    _backend_type = "odoo"

    name = fields.Char(required=True)

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
        """Available versions for this backend"""
        return [
            ("6.1", "Version 6.1.x"),
            ("10.0", "Version 10.0.x"),
            ("11.0", "Version 11.0.x"),
            ("12.0", "Version 12.0.x"),
        ]

    active = fields.Boolean(default=True)
    state = fields.Selection(selection="_select_state", default="draft")
    version = fields.Selection(selection="_select_versions", required=True)
    login = fields.Char(
        string="Username / Login",
        required=True,
        help="Username in the external Odoo Backend.",
    )
    password = fields.Char(required=True)
    database = fields.Char(required=True)
    hostname = fields.Char(required=True)
    port = fields.Integer(
        required=True,
        help="For SSL, 443 is mostly the right choice",
        default=8069,
    )
    protocol = fields.Selection(
        selection=[
            ("jsonrpc", "JsonRPC"),
            ("jsonrpc+ssl", "JsonRPC with SSL"),
            ("xmlrpc", "XMLRPC"),
            ("xmlrpc+ssl", "XMLRPC with SSL"),
        ],
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

    export_user_id = fields.Integer(
        string="User ID in the external System",
        help="""The user id that represents this company in the
                external system.""",
    )

    default_export_backend = fields.Boolean(
        help="Use this backend as an automatic export target.",
    )

    """
    PARTNER SYNC OPTIONS
    """

    default_export_partner = fields.Boolean("Export partner")
    default_import_partner = fields.Boolean("Import partner")

    local_partner_domain_filter = fields.Char(default="[]")

    external_partner_domain_filter = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination
        """,
    )

    """
    USER SYNC OPTIONS
    """

    default_export_user = fields.Boolean()
    default_import_user = fields.Boolean()

    local_user_domain_filter = fields.Char(default="[]")

    external_user_domain_filter = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination
        """,
    )

    """
    PRODUCT SYNC OPTIONS
    """

    matching_product_product = fields.Boolean(string="Match product", default=True)
    matching_product_ch = fields.Selection(
        [("default_code", "Reference"), ("barcode", "Barcode")],
        string="Matching Field for product",
        default="default_code",
        required=True,
    )
    matching_customer = fields.Boolean(
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
    work_with_variants = fields.Boolean(
        help="If not work with variants, when import product does not try to import template",
    )
    default_import_product = fields.Boolean("Import products")
    import_product_from_date = fields.Datetime()
    import_partner_from_date = fields.Datetime()
    import_user_from_date = fields.Datetime()
    import_categories_from_date = fields.Datetime()
    import_pricelist_items_from_date = fields.Datetime("Import pricelists from date")
    default_export_product = fields.Boolean("Export Products")
    export_products_from_date = fields.Datetime()
    export_categories_from_date = fields.Datetime()
    default_category_id = fields.Integer(
        help="If set, this Id will be used instead of getting dependencies",
    )
    default_product_export_dict = fields.Char(
        "Default Json for creating/updating products",
        default="{'default_code': '/', 'active': False}",
    )
    pricelist_id = fields.Many2one("product.pricelist", "Pricelist", required=True)
    main_record = fields.Selection(
        [
            ("odoo", "Odoo -> Backend"),
            ("backend", "Backend -> Odoo"),
        ],
        help="Direction of master data synchronization. Read from X write to Y (X -> Y)",
    )
    force = fields.Boolean(help="Execute import/export even if no changes in backend")
    ignore_translations = fields.Boolean()

    """
    Logistic SYNC OPTIONS
    """

    def _get_picking_in(self):
        pick_in = self.env.ref("stock.picking_type_in", raise_if_not_found=False)
        company = self.env.company
        if (
            not pick_in
            or not pick_in.sudo().active
            or pick_in.sudo().warehouse_id.company_id.id != company.id
        ):
            pick_in = self.env["stock.picking.type"].search(
                [
                    ("warehouse_id.company_id", "=", company.id),
                    ("code", "=", "incoming"),
                ],
                limit=1,
            )
        return pick_in

    read_operation_from = fields.Selection(
        [("backend", "Backend"), ("odoo", "Odoo")], default="backend", required=True
    )
    default_purchase_picking_type_id = fields.Many2one(
        "stock.picking.type",
        required=True,
        default=_get_picking_in,
        domain="['|',"
        + "('warehouse_id', '=', False),"
        + "('warehouse_id.company_id', '=', company_id)]",
    )
    default_import_purchase_order = fields.Boolean("Import purchase orders")
    import_purchase_order_from_date = fields.Datetime()
    default_import_sale_order = fields.Boolean("Import Sale orders")
    import_sale_order_from_date = fields.Datetime()
    delayed_import_lines = fields.Boolean(
        help="Import lines after import header document "
        "(sale, purchase or picking) on delayed jobs"
    )

    default_import_stock = fields.Boolean("Import Stock")
    import_stock_from_date = fields.Datetime()

    def get_default_language_code(self):
        lang = (
            self.default_lang_id.code
            or self.env.user.lang
            or self.env.context["lang"]
            or "en_US"
        )
        return lang

    def get_connection(
        self,
    ):
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
        return OdooAPI(odoo_location)

    def _check_connection(self):
        odoo_api = self.get_connection()
        odoo_api.complete_check()
        self.write({"state": "checked"})

    def button_check_connection(self):
        self._check_connection()

    def button_reset_to_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})

    @contextmanager
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
            with _super.work_on(model_name, odoo_api=odoo_api, **kwargs) as work:
                yield work

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
        except BaseException as e:
            _logger.error(e, exc_info=True)
            raise UserError(
                _(
                    "Check your configuration, we can't get the data. "
                    "Here is the error:\n%s"
                )
                % e
            ) from e

    # TODO: Add Checkpoing as native Odoo Activity
    def add_checkpoint(self, record):
        # self.ensure_one()
        # record.ensure_one()
        # return checkpoint.add_checkpoint(
        #     self.env, record._name, record.id, self._name, self.id
        # )
        return True

    def import_product_product(self):
        if not self.default_import_product:
            return False
        self._import_from_date("odoo.product.product", "import_product_from_date")
        return True

    def import_product_template(self):
        if not self.default_import_product:
            return False
        self._import_from_date("odoo.product.template", "import_product_from_date")
        return True

    def import_partner(self):
        if not self.default_import_partner:
            return False
        self._import_from_date("odoo.res.partner", "import_partner_from_date")
        return True

    def import_user(self):
        if not self.default_import_user:
            return False
        self._import_from_date("odoo.res.users", "import_user_from_date")
        return True

    def import_product_pricelist_item(self):
        if not self.default_import_product:
            return False
        self._import_from_date(
            "odoo.product.pricelist.item", "import_pricelist_items_from_date"
        )
        return True

    def import_product_categories(self):
        if not self.default_import_product:
            return False
        self._import_from_date("odoo.product.category", "import_categories_from_date")
        return True

    def import_purchase_orders(self):
        if not self.default_import_purchase_order:
            return False
        self._import_from_date("odoo.purchase.order", "import_purchase_order_from_date")
        return True

    def import_sale_orders(self):
        if not self.default_import_sale_order:
            return False
        self._import_from_date("odoo.sale.order", "import_sale_order_from_date")
        return True

    def import_locations(self):
        if not self.default_import_stock:
            return False
        self._import_from_date("odoo.stock.location", "import_stock_from_date")
        return True

    def import_pickings(self):
        if not self.default_import_stock:
            return False
        self._import_from_date("odoo.stock.picking", "import_stock_from_date")
        return True

    def import_stock_inventories(self):
        if not self.default_import_stock:
            return False
        self._import_from_date(
            "odoo.stock.inventory.disappeared", "import_stock_from_date"
        )
        return True

    def _import_from_date(self, model, from_date_field):
        import_start_time = datetime.now()
        filters = [("write_date", "<", fields.Datetime.to_string(import_start_time))]
        for backend in self:
            from_date = backend[from_date_field]
            if from_date:
                from_date = fields.Datetime.to_string(from_date)
                filters.append(
                    (
                        "write_date",
                        ">",
                        from_date,
                    )
                )
            else:
                from_date = None
            if self.version == "6.1":
                self.env[model].with_delay().import_batch(
                    backend, [("write_date", "=", False)]
                )
            self.env[model].with_delay().import_batch(backend, filters)

        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({from_date_field: next_time})

    def import_external_id(self, model, external_id, force, inmediate=False):
        model = self.env[model]
        if not inmediate:
            model = model.with_delay()
        for backend in self:
            model.import_record(backend, external_id, force)

    def export_product_categories(self):
        if not self.default_export_product:
            return False
        self._export_from_date("odoo.product.category", "export_categories_from_date")
        return True

    def export_product_products(self):
        if not self.default_export_product:
            return False
        self._export_from_date("odoo.product.product", "export_products_from_date")
        return True

    def export_product_templates(self):
        if not self.default_export_product:
            return False
        self._export_from_date("odoo.product.template", "export_products_from_date")
        return True

    def _export_from_date(self, model, from_date_field):
        self.ensure_one()
        import_start_time = datetime.now()
        filters = [("write_date", "<", fields.Datetime.to_string(import_start_time))]
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
