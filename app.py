import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, Kecamatan, Stok, Transaksi
from config import Config

# Load environment variables
load_dotenv()

# Buat aplikasi
app = create_app(Config)

if __name__ == '__main__':
    # Memeriksa debug mode dari env (bisa 'true', '1', atau 't')
    debug_val = os.environ.get('FLASK_DEBUG', 'false').lower()
    is_debug = debug_val in ['true', '1', 't']
    
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=is_debug, host='0.0.0.0', port=port)
