"""
Provides a Swagger (http://swagger.wordnik.com/) implementation
for flask-peewee rest apis.
"""

from __future__ import absolute_import

import logging, peewee
import os
from flask import jsonify, Blueprint, render_template
from flask.globals import request
from flask.ext.peewee_swagger import first

logger = logging.getLogger('flask_peewee_swagger')
current_dir = os.path.dirname(__file__)

class SwaggerUI(object):
    """ Adds a flask blueprint for the swagger ajax UI. """

    def __init__(self, app, title='api docs', prefix='/api-docs'):
        super(SwaggerUI, self).__init__()

        self.app = app
        self.title = title
        self.url_prefix = prefix

        self.blueprint = Blueprint('SwaggerUI', __name__,
            static_folder=os.path.join(current_dir, 'static'),
            template_folder=os.path.join(current_dir, 'templates'))

    def setup(self):
        self.blueprint.add_url_rule('/', 'index', self.index)
        self.app.register_blueprint(self.blueprint, url_prefix=self.url_prefix)

    def index(self):
        return render_template('swagger.jinja2',
            static_dir='%s/static' % self.url_prefix,
            title=self.title,
        )

class Swagger(object):
    """ Adds a flask blueprint for the swagger meta json resources. """

    def __init__(self, api, name='Swagger'):
        super(Swagger, self).__init__()

        self.app = api.app
        self.api = api

        self.blueprint = Blueprint(name, __name__)

    def setup(self):
        self.configure_routes()
        self.app.register_blueprint(self.blueprint, url_prefix='%s/meta' % self.api.url_prefix)

    def configure_routes(self):
        self.blueprint.add_url_rule('/resources',
            'model_resources', self.model_resources)
        self.blueprint.add_url_rule('/resources/<resource_name>',
            'model_resource', self.model_resource)

    def base_uri(self):
        base_uri = request.host_url
        if base_uri.endswith('/'):
            base_uri = base_uri[0:-1]
        return base_uri

    def model_resources(self):
        """ Listing of all supported resources. """

        response = jsonify({
            'apiVersion': '0.1',
            'swaggerVersion': '1.1',
            'basePath': '%s%s' % (self.base_uri(), self.api.url_prefix),
            'apis': self.get_model_resources()
        })

        response.headers.add('Cache-Control', 'max-age=0')
        return response

    def get_model_resources(self):
        resources = []

        for type in sorted(self.api._registry.keys(), key=lambda type: type.__name__):
            resource = self.api._registry.get(type)
            resources.append({
                'path': '/meta/resources/%s' % resource.get_api_name(),
                'description': 'Managed objects of type %s' % type.__name__
            })

        return resources

    def model_resource(self, resource_name):
        """ Details of a specific model resource. """

        resource = first(
            [resource for resource in self.api._registry.values()
             if resource.get_api_name() == resource_name])

        apis = []

        data = {
            'apiVersion': '0.1',
            'swaggerVersion': '1.1',
            'basePath': '%s%s' % (self.base_uri(), self.api.url_prefix),
            'resourcePath': '/meta/%s' % resource.get_api_name(),
            'apis': apis
        }

        self.add_get_all_api(apis, resource)
        self.add_get_item_api(apis, resource)

        response = jsonify(data)
        response.headers.add('Cache-Control', 'max-age=0')
        return response

    def add_get_all_api(self, apis, resource):
        """ Generates the meta descriptor for the resource listing api. """

        limit_param = {
            'paramType': 'query',
            'name': 'limit',
            'description': 'The number of items to return (defaults to 10)',
            'dataType': 'int',
            'required': False,
            'allowMultiple': False,
            }
        page_param = {
            'paramType': 'query',
            'name': 'page',
            'description': 'The page number of the results to return. Used '
                           'with limit.',
            'dataType': 'int',
            'required': False,
            'allowMultiple': False,
            }

        get_all_params = [
            limit_param,
            page_param
        ]

        for field_name in sorted(resource.model._meta.fields.keys()):
            field = resource.model._meta.fields.get(field_name)
            rules = field.attributes.get('rules')
            if rules and not rules.api.view:
                continue

            data_type = 'int'
            if isinstance(field, peewee.CharField):
                data_type = 'string'
            elif isinstance(field, peewee.DateTimeField):
                data_type = 'Date'
            elif isinstance(field, peewee.FloatField):
                data_type = 'float'
            elif isinstance(field, peewee.BooleanField):
                data_type = 'boolean'

            parameter = {
                'paramType': 'query', 'name': field_name,
                'description': 'Filter by %s' % field_name,
                'dataType': data_type, 'required': False,
                'allowMultiple': False,
                }

            get_all_params.append(parameter)

        get_all_api = {
            'path': '/%s/' % resource.get_api_name(),
            'description': 'Operations on %s' % resource.model.__name__,
            'operations': [{
                               'httpMethod': 'GET',
                               'nickname': 'getAll%ss' % resource.model.__name__,
                               'summary': 'Find %ss' % resource.model.__name__,
                               'parameters': get_all_params,
                               }]
        }
        apis.append(get_all_api)

    def add_get_item_api(self, apis, resource):
        """ Generates the meta descriptor for the resource item api. """

        get_item_api = {
            'path': '/%s/{id}' % resource.get_api_name(),
            'description': 'Operations on %s' % resource.model.__name__,
            'operations': [{
                               'httpMethod': 'GET',
                               'nickname': 'get%sById' % resource.model.__name__,
                               'summary': 'Find %s by its unique ID' %
                                          resource.model.__name__,
                               'parameters': [{
                                                  'paramType': 'path',
                                                  'name': 'id',
                                                  'description': 'ID of %s '
                                                                 'that to be fetch' % resource.model.__name__,
                                                  'dataType': 'int',
                                                  'required': True,
                                                  'allowMultiple': False,
                                                  }],
                               }]
        }

        apis.append(get_item_api)
