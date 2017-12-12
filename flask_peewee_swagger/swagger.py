"""
Provides a Swagger (http://swagger.wordnik.com/) implementation
for flask-peewee rest apis.
"""

from __future__ import absolute_import

import logging, peewee
import os
from flask import jsonify, Blueprint, render_template
from flask import request, make_response
from flask.ext.peewee_swagger import first
from functools import wraps

logger = logging.getLogger('flask_peewee_swagger')
current_dir = os.path.dirname(__file__)

DEFAULT_SWAGGER_VERSION = "1.1"



def _max_age_0(f):
    """This decorator adds the headers to force revalidation of the response"""
    def decorated_function(*args, **kwargs):
        resp = make_response(f(*args, **kwargs))
        resp.headers.add('Cache-Control', 'max-age=0')
        return resp
    return decorated_function

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
                               title=self.title)


class Swagger(object):
    """ Adds a flask blueprint for the swagger meta json resources. """

    def __init__(self,
                 api,
                 name='Swagger',
                 version="0.1",
                 swagger_version=None,
                 title=None):
        super(Swagger, self).__init__()

        self.app = api.app
        self.api = api
        self.swagger_version = swagger_version or self.app.config.get(
            "SWAGGER_VERSION", DEFAULT_SWAGGER_VERSION)
        self.version = version
        self.title = title or api.blueprint.name

        self.blueprint = Blueprint(name, __name__)

    def setup(self):
        self.configure_routes()
        self.app.register_blueprint(
            self.blueprint, url_prefix='%s/meta' % self.api.url_prefix)

    def configure_routes(self):
        self.blueprint.add_url_rule('/resources', 'model_resources', self.model_resources)
        self.blueprint.add_url_rule('/resources/<resource_name>', 'model_resource', self.model_resource)

    def base_uri(self):
        base_uri = request.host_url
        if base_uri.endswith('/'):
            base_uri = base_uri[0:-1]
        return base_uri

    def get_api_metadata(self):
        """Get common API meta data."""
        if self.swagger_version >= "2.0":
            return {
                "info": {
                    "version": self.version,
                    "title": self.title,
                },
                'swaggerVersion': self.swagger_version,
                "host": request.host,
                'basePath': self.api.url_prefix,
                "schemes": [
                    request.scheme,
                ],
            }

        return {
            'apiVersion': self.version,
            'swaggerVersion': self.swagger_version,
            'basePath': '%s%s' % (self.base_uri(), self.api.url_prefix),
        }

    @_max_age_0
    def model_resources(self):
        """ Listing of all supported resources. """
        meta = self.get_api_metadata()
        meta["paths" if self.version >= "2.0" else "apis"] = self.get_model_resources()
        return jsonify(meta)

    def get_model_resources(self):
        """Get model resource references."""

        if self.swagger_version >= "2.0":
            return [
                {
                    "$ref": self.api._registry.get(t).get_api_name()
                }
                for t in sorted(
                    self.api._registry.keys(), key=lambda t: t.__name__)
            ]

        resources = []

        for type in sorted(self.api._registry.keys(),
            key=lambda type: type.__name__):
            resource = self.api._registry.get(type)
            resources.append({
                'path': '/meta/resources/%s' % resource.get_api_name(),
                'description': 'Managed objects of type %s' % type.__name__
            })

        return resources

    @_max_age_0
    def model_resource(self, resource_name):
        """Details of a specific model resource."""

        resource = first(
            [resource for resource in self.api._registry.values()
             if resource.get_api_name() == resource_name])
        meta = self.get_api_metadata()

        if self.swagger_version >= "2.0":
            meta.update({
                "paths": self.get_model_apis(resource),
                "definitions": self.get_model(resource),
            })
        else:
            meta.update({
                "apis": self.get_model_apis(resource),
                "resourcePath": '/meta/%s' % resource.get_api_name(),
                "models": self.get_model(resource),
            })

        return jsonify(meta)

    def get_model_apis(self, resource):
        return (
            self.get_listing_api(resource),
            self.get_item_api(resource),
            self.get_create_api(resource),
            self.get_update_api(resource),
            self.get_delete_api(resource)
        )

    def get_create_api(self, resource):
        """Generates the meta descriptor for the resource listing api."""

        create_api = {
            'path': '/%s/' % resource.get_api_name(),
            'description': 'Operations on %s' % resource.model.__name__,
            'operations': [
                {
                    'httpMethod': 'POST',
                    'nickname': 'create%ss' % resource.model
                    .__name__,
                    'summary': 'Create %ss' % resource.model.__name__,
                    'parameters': [{
                        'description': '%s object' % (resource.model.__name__),
                        'paramType': 'body',
                        'required': True,
                        'allowMultiple': False,
                        'dataType': resource.model.__name__
                    }]
                }
            ]
        }

        return create_api

    def get_update_api(self, resource):
        """ Generates the meta descriptor for the resource listing api. """

        update_api = {
            'path': '/%s/{id}/' % resource.get_api_name(),
            'description': 'Operations on %s' % resource.model.__name__,
            'operations': [
                {
                    'httpMethod': 'PUT',
                    'nickname': 'update%ss' % resource.model
                    .__name__,
                    'summary': 'Update %ss' % resource.model.__name__,
                    'parameters': [
                        {
                            'paramType': 'path',
                            'name': 'id',
                            'description': '%s id' % (resource.model.__name__),
                            'dataType': 'int',
                            'required': True,
                            'allowMultiple': False,
                        },
                        {
                            'description': '%s object' % (resource.model.__name__),
                            'paramType': 'body',
                            'required': True,
                            'allowMultiple': False,
                            'dataType': resource.model.__name__
                        }
                    ]
                }
            ]
        }

        return update_api

    def get_listing_api(self, resource):
        """ Generates the meta descriptor for the resource listing api. """

        get_all_params = self.get_listing_parameters(resource)

        get_all_api = {
            'path': '/%s/' % resource.get_api_name(),
            'description': 'Operations on %s' % resource.model.__name__,
            'operations': [
                {
                    'httpMethod': 'GET',
                    'nickname': 'list%ss' % resource.model
                    .__name__,
                    'summary': 'Find %ss' % resource.model.__name__,
                    'parameters': get_all_params,
                }
            ]
        }

        return get_all_api

    def get_listing_parameters(self, resource):
        params = []

        for field_name in sorted(resource.model._meta.fields.keys()):
            field = resource.model._meta.fields.get(field_name)
            parameter = self.get_model_field_parameter(resource, field)
            if parameter:
                params.append(parameter)


        params.append({
            'paramType': 'query',
            'name': 'limit',
            'description': 'The number of items to return (defaults to %s)' % resource.paginate_by,
            'dataType': 'int',
            'required': False,
            'allowMultiple': False,
        })

        params.append({
            'paramType': 'query',
            'name': 'page',
            'description': 'The page number of the results to return. Used '
                           'with limit.',
            'dataType': 'int',
            'required': False,
            'allowMultiple': False,
        })

        return params

    def get_model(self, resource):
        properties = {}

        if self.swagger_version >= "2.0":
            meta = resource.model._meta
            for field_name in sorted(meta.fields.keys()):
                field = meta.fields.get(field_name)
                model_property = self.get_model_property_v20(resource, field)
                if model_property:
                    properties[field_name] = model_property
            return {
                resource.model.__name__: {
                    "type": "object",
                    "properties": properties,
                }
            }

        for field_name in sorted(resource.model._meta.fields.keys()):
            field = resource.model._meta.fields.get(field_name)
            model_property = self.get_model_property(resource, field)
            if model_property:
                properties[field_name] = model_property
        return {
            resource.model.__name__: {
                'id': resource.model.__name__,
                'properties': properties
            }
        }

    def get_model_property_v20(self, resource, field):
        """Map model field to object property."""
        data_type = "integer"
        data_format = None
        if isinstance(field, (peewee.CharField, peewee.FixedCharField, peewee.TextField, )):
            data_type = "string"
        elif isinstance(field, peewee.BlobField):
            data_type = "string"
            data_format ="binary"
        elif isinstance(field, peewee.DateTimeField):
            data_type = "string"
            data_format ="date-time"
        elif isinstance(field, peewee.DateField):
            data_type = "string"
            data_format ="date"
        elif isinstance(field, peewee.FloatField):
            data_type = "number"
            data_format = "float"
        elif isinstance(field, peewee.DoubleField):
            data_type = "number"
            data_format = "double"
        elif isinstance(field, peewee.DecimalField):
            data_type = "number"
            data_format = "decimal"
        elif isinstance(field, peewee.BooleanField):
            data_type = "boolean"
        elif isinstance(field, peewee.BigIntegerField):
            data_type = "integer"
            data_format = "int64"
        elif isinstance(field, peewee.IntegerField):
            data_type = "integer"
            data_format = "int32"
        elif isinstance(field, peewee.UUIDField):
            data_type = "string"
            data_format = "uuid"

        property = {
            "type": data_type,
        }
        if data_format:
            property["format"] = data_format
        return property

    def get_model_property(self, resource, field):
        data_type = 'int'
        if isinstance(field, peewee.CharField):
            data_type = 'string'
        elif isinstance(field, peewee.DateTimeField):
            data_type = 'Date'
        elif isinstance(field, peewee.FloatField):
            data_type = 'float'
        elif isinstance(field, peewee.BooleanField):
            data_type = 'boolean'
        property = {
            'type':data_type,
        }
        return property

    def get_model_field_parameter(self, resource, field):
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
            'paramType': 'query', 'name': field.name,
            'description': 'Filter by %s' % field.name,
            'dataType': data_type, 'required': False,
            'allowMultiple': False,
        }
        return parameter

    def get_item_api(self, resource):
        """ Generates the meta descriptor for the resource item api. """

        parameters = self.get_item_parameters(resource)

        get_item_api = {
            'path': '/%s/{id}' % resource.get_api_name(),
            'description': 'Operations on %s' % resource.model.__name__,
            'operations': [
                {
                    'httpMethod': 'GET',
                    'nickname': 'get%s' % resource.model.__name__,
                    'summary': 'Get %s by its unique ID' %
                               resource.model.__name__,
                    'parameters': parameters,
                }
            ]
        }

        return get_item_api

    def get_item_parameters(self, resource):
        return [{
            'paramType': 'path',
            'name': 'id',
            'description': 'ID of %s to be fetched' % resource.model.__name__,
            'dataType': 'int',
            'required': True,
            'allowMultiple': False,
        }]

    def get_delete_api(self, resource):
        """ Generates the meta descriptor for the resource item api. """

        parameters = self.delete_item_parameters(resource)

        get_item_api = {
            'path': '/%s/{id}/' % resource.get_api_name(),
            'description': 'Operations on %s' % resource.model.__name__,
            "responseClass": "void",
            'operations': [
                {
                    'httpMethod': 'DELETE',
                    'nickname': 'delete%s' % resource.model.__name__,
                    'summary': 'Delete %s by its unique ID' %
                               resource.model.__name__,
                    'parameters': parameters,
                }
            ]
        }

        return get_item_api

    def delete_item_parameters(self, resource):
        return [{
            'paramType': 'path',
            'name': 'id',
            'description': 'ID of %s to be fetched' % resource.model.__name__,
            'dataType': 'int',
            'required': True,
            'allowMultiple': False,
        }]

        return delete_item_api
