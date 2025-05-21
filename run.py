import os
from dotenv import load_dotenv
from app import create_app

load_dotenv() # Load environment variables from .env

config_name = os.environ.get('FLASK_CONFIG') or 'development'
app = create_app(config_name)

if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', True))