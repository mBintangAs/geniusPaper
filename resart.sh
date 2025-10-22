#!/bin/bash

# -----------------------------------------------------------------
# GANTI INI DENGAN NAMA SERVIS SYSTEMD GUNICORN ANDA
GUNICORN_SERVICE="gpaper.service"
# -----------------------------------------------------------------


# 1. Cek apakah script dijalankan dengan sudo
if [ "$EUID" -ne 0 ]; then
  echo "Harap jalankan script ini dengan sudo:"
  echo "sudo ./restart.sh"
  exit 1
fi

# 2. Restart Gunicorn
echo "-----------------------------------"
echo "Merestart Gunicorn ($GUNICORN_SERVICE)..."
systemctl restart $GUNICORN_SERVICE
echo "Gunicorn telah di-restart."
echo "-----------------------------------"
sleep 1

# 3. Tes Konfigurasi Nginx
echo "Mentes konfigurasi Nginx..."
nginx -t

# $? adalah kode status dari perintah terakhir (nginx -t)
# 0 = sukses, selain itu = gagal
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Konfigurasi Nginx GAGAL (ada typo/kesalahan)."
    echo "Nginx TIDAK di-reload untuk mencegah error."
    exit 1
fi

# 4. Reload Nginx (jika tes berhasil)
echo ""
echo "Konfigurasi Nginx OK."
echo "Me-reload Nginx..."
systemctl reload nginx
echo "Nginx telah di-reload."
echo "-----------------------------------"
echo "Semua servis telah diperbarui!"
