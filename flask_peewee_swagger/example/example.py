from flask import Flask
from flask.ext.peewee.rest import RestAPI, RestResource
from peewee import Model
import peewee
from flask.ext.peewee_swagger.swagger import Swagger, SwaggerUI

app = Flask(__name__)

class Blog(Model):
    title = peewee.CharField()
    created = peewee.DateTimeField()
    modified = peewee.DateTimeField()

class Post(Model):
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

swagger = Swagger(api)
swagger.setup()

swaggerUI = SwaggerUI(app)
swaggerUI.setup()

if __name__ == '__main__':
    app.run()

