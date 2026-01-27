from flask import Blueprint, render_template
from app.models import Kecamatan, Stok
from sqlalchemy import func

# Ini mendefinisikan "public_bp" yang dicari oleh __init__.py
public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    # Get total stock for Disdukcapil Garut
    total_stok_ktp = Stok.query.with_entities(func.sum(Stok.jumlah_ktp)).scalar() or 0
    
    # Get active kecamatan (those with stock > 0)
    active_kecamatan = Stok.query.filter(Stok.jumlah_ktp > 0).count()
    
    # Get stock data for all kecamatan
    stock_data = []
    for row in Stok.query.join(Kecamatan).with_entities(
        Kecamatan.nama_kecamatan,
        Stok.jumlah_ktp,
        Stok.last_updated
    ).all():
        stock_data.append({
            'nama_kecamatan': row.nama_kecamatan,
            'jumlah_ktp': row.jumlah_ktp,
            'last_updated': row.last_updated.strftime('%d/%m/%Y %H:%M') if row.last_updated else '-'
        })
    
    return render_template('public/index.html', 
                         total_stok_ktp=total_stok_ktp,
                         active_kecamatan=active_kecamatan,
                         stock_data=stock_data)