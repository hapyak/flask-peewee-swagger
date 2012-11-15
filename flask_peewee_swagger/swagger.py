from __future__ import absolute_import

import logging, peewee
import os
from flask import jsonify, Blueprint, render_template
from flask.globals import request
from flask.ext.peewee_swagger import first

logger = logging.getLogger('flask_peewee_swagger')
current_dir = os.path.dirname(__file__)

class SwaggerUI(object):
    def __init__(self, app, name='swagger', prefix='/api-docs'):
        super(SwaggerUI, self).__init__()

        self.app = app
        self.url_prefix = prefix
        self.blueprint = Blueprint(name, __name__,
            static_folder=os.path.join(current_dir, 'static'),
            template_folder=os.path.join(current_dir, 'templates'))

        self.blueprint.add_url_rule('/', 'index', self.index)
        self.app.register_blueprint(self.blueprint, url_prefix=self.url_prefix)

    def index(self):
        return render_template('swagger.jinja2')

class Swagger(object):
    def __init__(self, api, name='swagger'):
        super(Swagger, self).__init__()

        self.app = api.app
        self.api = api

        self.blueprint = Blueprint(name, __name__)

        self.blueprint.add_url_rule('resources',
            'model_resources', self.model_resources)
        self.blueprint.add_url_rule('resources/<resource_name>',
            'model_resource', self.model_resource)

        self.app.register_blueprint(self.blueprint, url_prefix='%s/meta' % self.api.url_prefix)

    def base_uri(self):
        base_uri = request.host_url
        if base_uri.endswith('/'):
            base_uri = base_uri[0:-1]
        return base_uri

    def model_resources(self):
        """
        Resource for generating swagger documentation.
        http://swagger.wordnik.com/
        """

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
        """
        Resource for generating swagger documentation.
        http://swagger.wordnik.com/
        """

        resource = first(
            [resource for resource in self.api._registry.values()
             if resource.get_api_name() == resource_name])

        apis = []
        models = {}

        data = {
            'apiVersion': '0.1',
            'swaggerVersion': '1.1',
            'basePath': '%s%s' % (self.base_uri(), self.api.url_prefix),
            'resourcePath': '/meta/%s' % resource.get_api_name(),
            'apis': apis,
            'models': models
        }

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
            'description': 'The page number of the results to return. Used with limit.',
            'dataType': 'int',
            'required': False,
            'allowMultiple': False,
        }

        get_all_params = [
            limit_param,
            page_param
        ]

        for field_name in sorted(resource.type._meta.fields.keys()):
            field = resource.type._meta.fields.get(field_name)
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
            'description': 'Operations on %s' % resource.type.__name__,
            'operations': [{
                'httpMethod': 'GET',
                'nickname': 'getAll%ss' % resource.type.__name__,
                'summary': 'Find %ss' % resource.type.__name__,
                'parameters': get_all_params,
            }]
        }

        apis.append(get_all_api)

        get_item_api = {
            'path': '/%s/{id}' % resource.get_api_name(),
            'description': 'Operations on %s' % resource.type.__name__,
            'operations': [{
                'httpMethod': 'GET',
                'nickname': 'get%sById' % resource.type.__name__,
                'summary': 'Find %s by its unique ID' % resource.type.__name__,
                'responseClass': 'Video',
                'parameters': [{
                    'paramType': 'path',
                    'name': 'id',
                    'description': 'ID of %s that to be fetch' % resource.type.__name__,
                    'dataType': 'int',
                    'required': True,
                    'allowMultiple': False,
                }],
            }]
        }

        apis.append(get_item_api)

        response = jsonify(data)
        response.headers.add('Cache-Control', 'max-age=0')
        return response
