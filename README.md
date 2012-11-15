flask-peewee-swagger
====================

Generates [swagger](http://http://swagger.wordnik.com/) documentation for [flask-peewee](https://github.com/coleifer/flask-peewee) projects.

### Flask Routes

Two base routes will be added to your flask application to support swagger documentation.

    /api-docs/ - The Swagger UI dynamic API docs
    /api/meta/ - The Swagger json meta end points

### Example

	import peewee
	from peewee import Model
	from flask import Flask
	from flask.ext.peewee.rest import RestAPI, RestResource
	from flask.ext.peewee_swagger.swagger import Swagger, SwaggerUI

	######################################
	# standard flask peewee setup	
	######################################

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
	
	######################################
	# create the swagger api end point
	######################################

	swagger = Swagger(api)
	swagger.setup()
	
	# create the Swagger user interface endpoint
	swaggerUI = SwaggerUI(app)
	swaggerUI.setup()
	
	if __name__ == '__main__':
	    app.run()
	
