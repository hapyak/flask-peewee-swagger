from __future__ import absolute_import

from flask import Flask
import peewee
from flask_peewee.rest import RestAPI, RestResource
from flask_peewee_swagger.swagger import Swagger, SwaggerUI
from faker import Faker
from datetime import datetime

######################################
# standard flask peewee setup
######################################

app = Flask(__name__)
db = peewee.SqliteDatabase("example.db")


class Authentication(object):
    def authorize(self):
        return True

class Blog(peewee.Model):
    title = peewee.CharField()
    created = peewee.DateTimeField(default=datetime.now)
    modified = peewee.DateTimeField(null=True)

    class Meta:
        database = db


class Post(peewee.Model):
    blog = peewee.ForeignKeyField(Blog, related_name="posts")
    title = peewee.CharField()

    class Meta:
        database = db


@app.cli.command("initdb")
def initdb():
    """Create a test DB and add some test data."""
    Post.drop_table(fail_silently=True)
    Blog.drop_table(fail_silently=True)
    Blog.create_table()
    Post.create_table()
    faker = Faker()
    for i in range(1, 10):
        b = Blog.create(title = "Blog #%d" % i)
        Post.insert_many([{
            "blog": b,
            "title": faker.text(max_nb_chars=80),
        } for _ in range(100)]).execute()


class BlogResource(RestResource):
    pass


class PostResource(RestResource):
    pass


api = RestAPI(app)
api.register(Blog, BlogResource, Authentication())
api.register(Post, PostResource, Authentication())
api.setup()

######################################
# create the swagger api end point
######################################

swagger = Swagger(api)
swagger.setup()

swagger2 = Swagger(api, version="1.1", swagger_version="2.0", name="spec2")
swagger2.setup(prefix="spec2")

swaggerUI = SwaggerUI(app)
swaggerUI.setup()

if __name__ == '__main__':
    app.run()
