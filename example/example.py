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



class BlogResource(RestResource):
    pass


class PostResource(RestResource):
    pass


api = RestAPI(app)
api.register(Blog, BlogResource)
api.register(Post, PostResource)
api.setup()

api2 = RestAPI(app, prefix="/api2", name="api2")
api2.register(Blog, BlogResource)
api2.register(Post, PostResource)
api2.setup()

######################################
# create the swagger api end point
######################################

swagger = Swagger(api)
swagger.setup()

swagger2 = Swagger(api2, version="1.1", swagger_version="2.0", name="spec2")
swagger2.setup()

swaggerUI = SwaggerUI(app)
swaggerUI.setup()

if __name__ == '__main__':
    app.run()

