# -*- coding: utf-8 -*-
# Copyright 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models


@api.model
@api.returns('self', lambda value: value.id)
def o2o_create(self, vals):
    return models.BaseModel.create(self, vals)


@api.v8
def o2o_read(self, fields=None, load='_classic_read'):
    return models.BaseModel.read(self, fields, load)


@api.multi
def o2o_write(self, vals):
    return models.BaseModel.write(self, vals)


@api.multi
def o2o_unlink(self):
    return models.BaseModel.unlink(self)


def post_load():
    models.BaseModel.o2o_create = o2o_create
    models.BaseModel.o2o_read = o2o_read
    models.BaseModel.o2o_write = o2o_write
    models.BaseModel.o2o_unlink = o2o_unlink
