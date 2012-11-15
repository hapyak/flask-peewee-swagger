from __future__ import absolute_import

from flask import Flask
import peewee
from flask_peewee.rest import RestAPI, RestResource
from flask_peewee_swagger.swagger import Swagger, SwaggerUI

######################################
# standard flask peewee setup
######################################

app = Flask(__name__)

class Blog(peewee.Model):
    title = peewee.CharField()
    created = peewee.DateTimeField()
    modified = peewee.DateTimeField()

class Post(peewee.Model):
    blog = peewee.ForeignKeyField(Blog, related_name='posts')
    title = peewee.CharField()

api = RestAPI(app)

class BlogResource(RestResource):
    pass

class PostResource(RestResource):
    pass

api.register(Blog, BlogResource)
api.register(Post, PostResource)

api.setup()

######################################
# create the swagger api end point
######################################

swagger = Swagger(api)
swagger.setup()

swaggerUI = SwaggerUI(app)
swaggerUI.setup()

if __name__ == '__main__':
    app.run()

