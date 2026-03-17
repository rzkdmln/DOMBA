from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Regexp, ValidationError
import re

class LaporPakaiForm(FlaskForm):
    nik = StringField('NIK', validators=[
        DataRequired(message='NIK wajib diisi!'),
        Regexp(r'^\d{16}$', message='NIK harus terdiri dari 16 digit angka!')
    ])
    nama_lengkap = StringField('Nama Lengkap', validators=[
        DataRequired(message='Nama Lengkap wajib diisi!'),
        Regexp(r'^[A-Z\s\'\-]+$', message='Nama Lengkap hanya boleh huruf kapital, spasi, dash, atau kutip!')
    ])
    jenis_cetak = SelectField('Jenis Cetak', choices=[
        ('Cetak Baru', 'Cetak Baru'),
        ('Hilang', 'Hilang'),
        ('Rusak', 'Rusak'),
        ('Perubahan Data', 'Perubahan Data')
    ], validators=[DataRequired(message='Jenis Cetak wajib diisi!')])
    
    registrasi_ikd = SelectField('Registrasi IKD', choices=[
        ('true', 'Ya'),
        ('false', 'Tidak')
    ], validators=[DataRequired(message='Status IKD wajib diisi!')])
    
    status_cetak = SelectField('Status Cetak', choices=[
        ('BERHASIL', 'BERHASIL'),
        ('GAGAL', 'GAGAL')
    ], default='BERHASIL')
    
    keterangan_gagal = TextAreaField('Keterangan Gagal')

    def validate_keterangan_gagal(self, field):
        if self.status_cetak.data == 'GAGAL' and not field.data:
            raise ValidationError('Keterangan gagal wajib diisi jika status cetak GAGAL!')
