# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import socket
import logging
import xmlrpclib

import odoorpc 
from odoorpc.error import RPCError
from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.connector.exception import NetworkRetryableError
from odoo.exceptions import UserError
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    import odoorpc as odoorpc
except ImportError:
    _logger.debug("Cannot import 'odoorpc' Lib")

class OdooLocation(object):
    def __init__(self, hostname, login, password,
                 database, port, version, protocol, lang_id='en_US',
                 use_custom_api_path=False):
      
        self.hostname = hostname
        self.login = login
        self.password = password
        self.database = database
        self.port = port
        self.version = version
        self.protocol = protocol
        self.lang_id = lang_id

class OdooAPI(object):

    def __init__(self, location):
        """
        :param location: Odoo location
        :type location: :class:`OdooLocation`
        """
        self._location = location
        self._api = None

    @property
    def api(self):
        if self._api is None:
            api = odoorpc.ODOO(
                host=self._location.hostname,
                port=self._location.port,
                protocol=self._location.protocol,
            )
            try:
                api.login(
                    db = self._location.database,
                    login = self._location.login,
                    password= self._location.password)
                    
            except odoorpc.error.RPCError as e:
                _logger.exception(e)
                raise UserError(e)
            
            self._api = api
            _logger.info('Created a new Odoo API instance and logged In')
            if self._location.lang_id:
                self._api.env.context['lang']= self._location.lang_id
        return self._api

    def complete_check(self):
        api = self.api
        if api.version != self._location.version:
            raise UserError(_('Server indicates version %s. Please adapt your conf' % api.version))
        
        try:
            api.login(
                db = self._location.database,
                login = self._location.login,
                password= self._location.password)
                
        except odoorpc.error.RPCError as e:
            _logger.exception(e)
            raise UserError(e)
                 
        
    def __enter__(self):
        # we do nothing, api is lazy
        return self
  
    def __exit__(self, type, value, traceback):
#         if self._api is not None:
#             self._api.__exit__(type, value, traceback)
        _logger.debug(traceback)
#         self.__exit__(type, value, traceback)

    

 
class OdooCRUDAdapter(AbstractComponent):
    """ External Records Adapter for Odoo """
 
    _name = 'odoo.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.odoo.connector']
    _usage = 'backend.adapter'
 
    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError
 
    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError
 
    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError
 
    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError
 
    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError
 
    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError
    
    def execute(self, id, data ):
        """ Execute method for a record on the external system """
        raise NotImplementedError
 
 
class GenericAdapter(AbstractComponent):
    _name = 'odoo.adapter'
    _inherit = 'odoo.crud.adapter'
 
#     _odoo_model = None
#     _admin_path = None
 
    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids
 
        :rtype: list
        """
        
        try:
            odoo_api = getattr(self.work, 'odoo_api')
            odoo_api = odoo_api.api
        except AttributeError:
            raise AttributeError(
                'You must provide a odoo_api attribute with a '
                'OdooAPI instance to be able to use the '
                'Backend Adapter.'
            )
        
        model = odoo_api.env[self._odoo_model]
        return model.search([filters] if filters else [])

 
    def read(self, id, attributes=None):
        """ Returns the information of a record
  
        :rtype: dict
        """
        arguments = [int(id)]
        if attributes:
            # Avoid to pass Null values in attributes. Workaround for
            # https://bugs.launchpad.net/openerp-connector-Odoo/+bug/1210775
            # When Odoo is installed on PHP 5.4 and the compatibility patch
            # http://odoo.com/blog/Odoo-news/Odoo-now-supports-php-54
            # is not installed, calling info() with None in attributes
            # would return a wrong result (almost empty list of
            # attributes). The right correction is to install the
            # compatibility patch on odoo.
            arguments.append(attributes)
        
        try:
            odoo_api = getattr(self.work, 'odoo_api')
            odoo_api = odoo_api.api
        except AttributeError:
            raise AttributeError(
                'You must provide a odoo_api attribute with a '
                'OdooAPI instance to be able to use the '
                'Backend Adapter.'
            )
        model = odoo_api.env[self._odoo_model]
        return model.browse(arguments)
 
#     def search_read(self, filters=None):
#         """ Search records according to some criterias
#         and returns their information"""
#         return self._call('%s.list' % self._odoo_model, [filters])
#  
#     def create(self, data):
#         """ Create a record on the external system """
#         return self._call('%s.create' % self._odoo_model, [data])
#  
#     def write(self, id, data):
#         """ Update records on the external system """
#         return self._call('%s.update' % self._odoo_model,
#                           [int(id), data])
#  
#     def delete(self, id):
#         """ Delete a record on the external system """
#         return self._call('%s.delete' % self._odoo_model, [int(id)])


