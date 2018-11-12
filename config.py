import os
from os.path import join, dirname

SECRET_KEY = os.environ.get('SECRET_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
REDIS_URL = os.environ.get('REDIS_URL')
