# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging

from odoo import api, fields, models
from odoo.addons.component.core import Component
# from odoo.addons.queue_job.job import job
# from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__name__)


class OdooPartner(models.Model):
    _name = "odoo.res.partner"
    _inherit = "odoo.binding"
    _inherits = {"res.partner": "odoo_id"}
    _description = "External Odoo Partner"

    @api.multi
    def name_get(self):
        result = []
        for op in self:
            name = "{} (Backend: {})".format(
                op.odoo_id.display_name, op.backend_id.display_name
            )
            result.append((op.id, name))

        return result


class Partner(models.Model):
    _inherit = "res.partner"

    bind_ids = fields.One2many(
        comodel_name="odoo.res.partner",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )

    @api.model
    def create(self, vals):
        record = super(Partner, self).create(vals)
        # FIXME: do the proper way
        bind_model = self.env['odoo.res.partner']
        backend = self.env['odoo.backend'].search([])
        bind_model.create({
            "backend_id": backend[0].id,
            "odoo_id": record.id,
            "external_id": 0,
        })
        return record


class PartnerAdapter(Component):
    _name = "odoo.res.partner.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.res.partner"

    _odoo_model = "res.partner"

    def search(self, filters=None, model=None):
        """ Search records according to some criteria
        and returns a list of ids

        :rtype: list
        """
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_partner_domain_filter)
        )
        filters += ext_filter
        return super(PartnerAdapter, self).search(filters=filters, model=model)


class PartnerListener(Component):
    _name = 'odoo.res.partner.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['odoo.res.partner']
    _usage = 'event.listener'

    # @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record(backend=record.backend_id)

    def on_record_write(self, record, fields=None):
        record.with_delay().export_record(backend=record.backend_id)
