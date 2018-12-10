import os


# URL of api app (on AWS this is the internal api endpoint)
API_HOST_NAME = os.getenv('API_HOST_NAME')

# admin app api key
ADMIN_CLIENT_SECRET = os.getenv('ADMIN_CLIENT_SECRET')

# encyption secret/salt
SECRET_KEY = os.getenv('SECRET_KEY')
DANGEROUS_SALT = os.getenv('DANGEROUS_SALT')

# DB conection string
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
