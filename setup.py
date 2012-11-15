import sys
from setuptools import setup, find_packages

requirements = ['Flask', 'werkzeug', 'jinja2', 'peewee>2.0.0', 'wtforms', 'wtf-peewee', 'flask-peewee']
if sys.version_info[:2] < (2, 6):
    requirements.append('simplejson')

setup(
    name='flask-peewee-swagger',
    version='0.0.1',
    url='http://github.com/hapyak/flask-peewee-swagger/',
    license='BSD',
    author='Jason Horman',
    author_email='jhorman@hapyak.com',
    description='Swagger Documentation for flask-peewee apis',
    packages=find_packages(),
    package_data = {
        'flask_peewee_swagger': [
            'static/swagger-ui-1.1.0/css/*.css',
            'static/swagger-ui-1.1.0/images/*.png',
            'static/swagger-ui-1.1.0/lib/*.js',
            'static/swagger-ui-1.1.0/*.js',
            'templates/*.jinja2'
        ],
    },
    zip_safe=False,
    platforms='any',
    install_requires=requirements,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
