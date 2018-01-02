# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from openerp.addons.odoo2odoo_backend.tests.common import SetUpOdooBase

logger = logging.getLogger(__name__)


class TestProduct(SetUpOdooBase):

    def test_export(self):
        logger.info(
            u"BEFORE - COUNT(PRODUCTS) = %s",
            self.env['product.product'].search_count([]))
        logger.info(
            u"BEFORE - COUNT(JOBS) = %s",
            self.env['queue.job'].search_count([]))
        vals = {
            'name': u"ODOO2ODOO TEST",
            'default_code': u"ODOO2ODOO_TEST",
        }
        nb_jobs_before = self.env['queue.job'].search_count([])
        product = self.env['product.product'].create(vals)
        self.assertTrue(bool(product.odoo_bind_ids))
        nb_jobs_after = self.env['queue.job'].search_count([])
        self.assertTrue(nb_jobs_after > nb_jobs_before)
