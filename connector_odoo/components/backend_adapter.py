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
                 database, port, version, protocol,
                 use_custom_api_path=False):
      
        self.hostname = hostname
        self.login = login
        self.password = password
        self.database = database
        self.port = port
        self.version = version
        self.protocol = protocol

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
            self._api = api
            _logger.info('Created a new Odoo API instance')
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
        if self._api is not None:
            self._api.__exit__(type, value, traceback)
#         self.__exit__(type, value, traceback)

    def call(self, method, arguments):
        try:
            if isinstance(arguments, list):
                while arguments and arguments[-1] is None:
                    arguments.pop()
            start = datetime.now()
            try:
                result = self.api.execute(method, arguments)
            except:
                _logger.error("api.call('%s', %s) failed", method, arguments)
                raise
            else:
                _logger.debug("api.call('%s', %s) returned %s in %s seconds",
                              method, arguments, result,
                              (datetime.now() - start).seconds)
            # Uncomment to record requests/responses in ``recorder``
            # record(method, arguments, result)
            return result
        except (socket.gaierror, socket.error, socket.timeout) as err:
            raise NetworkRetryableError(
                'A network error caused the failure of the job: '
                '%s' % err)
        except xmlrpclib.ProtocolError as err:
            if err.errcode in [502,   # Bad gateway
                               503,   # Service unavailable
                               504]:  # Gateway timeout
                raise RetryableJobError(
                    'A protocol error caused the failure of the job:\n'
                    'URL: %s\n'
                    'HTTP/HTTPS headers: %s\n'
                    'Error code: %d\n'
                    'Error message: %s\n' %
                    (err.url, err.headers, err.errcode, err.errmsg))
            else:
                raise

 
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
 
    def _call(self, method, arguments):
        try:
            odoo_api = getattr(self.work, 'odoo_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a odoo_api attribute with a '
                'OdooAPI instance to be able to use the '
                'Backend Adapter.'
            )
        return odoo_api.call(method, arguments)
 
 
class GenericAdapter(AbstractComponent):
    _name = 'odoo.adapter'
    _inherit = 'odoo.crud.adapter'
 
    _odoo_model = None
    _admin_path = None
 
    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids
 
        :rtype: list
        """
        return self._call('%s.search' % self._Odoo_model,
                          [filters] if filters else [{}])
 
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
        return self._call('%s.info' % self._Odoo_model,
                          arguments)
 
    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        return self._call('%s.list' % self._Odoo_model, [filters])
 
    def create(self, data):
        """ Create a record on the external system """
        return self._call('%s.create' % self._Odoo_model, [data])
 
    def write(self, id, data):
        """ Update records on the external system """
        return self._call('%s.update' % self._Odoo_model,
                          [int(id), data])
 
    def delete(self, id):
        """ Delete a record on the external system """
        return self._call('%s.delete' % self._Odoo_model, [int(id)])


