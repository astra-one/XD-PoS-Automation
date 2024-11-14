import os
import pandas as pd
from pyzbar.pyzbar import decode
from PIL import Image
from datetime import datetime
import re

# Pasta onde os QR Codes estão armazenados
QR_CODES_FOLDER = "qr-codes"

# Lista para armazenar os dados
data = []

# Número de telefone do WhatsApp
WHATSAPP_PHONE_NUMBER = "551132803247"


# Função para extrair o shortUrl do QR Code
def get_short_url(image_path):
    img = Image.open(image_path)
    decoded_objects = decode(img)
    for obj in decoded_objects:
        return obj.data.decode("utf-8")
    return None


# Função para extrair o número da mesa a partir do nome do arquivo
def get_table_number_from_filename(filename):
    # Usa expressões regulares para encontrar o número após 'mesa' no nome do arquivo
    match = re.search(r"mesa[-_]?(\d+)", filename, re.IGNORECASE)
    if match:
        return match.group(1)
    else:
        print(f"Não foi possível extrair o número da mesa do arquivo {filename}")
        return None


# Processar cada arquivo na pasta
for filename in os.listdir(QR_CODES_FOLDER):
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        image_path = os.path.join(QR_CODES_FOLDER, filename)

        # Extrair o shortUrl
        short_url = get_short_url(image_path)
        if not short_url:
            print(f"Não foi possível decodificar o QR Code em {filename}")
            continue

        # Extrair o shortCode a partir do shortUrl
        short_code = short_url.split("/")[-1]

        # Extrair o número da mesa a partir do nome do arquivo
        table_number = get_table_number_from_filename(filename)
        if not table_number:
            continue

        # Construir o longUrl
        message = f"Gostaria de pagar a comanda {table_number}!"
        encoded_message = message.replace(" ", "%20")
        long_url = f"https://wa.me/{WHATSAPP_PHONE_NUMBER}?text={encoded_message}"

        # Montar os dados
        # Compile the data
        record = {
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "domain": "coti.a2csolutions.com.br",
            "shortCode": short_code,
            "shortUrl": short_url,
            "longUrl": long_url,
            "title": f"Whatsapp-{table_number}",
            "tags": f"comanda,{table_number},pague-sua-conta",  # Define tags as a list of strings
            "visits": 0,
        }

        data.append(record)
    else:
        continue

# Criar o DataFrame
df = pd.DataFrame(
    data,
    columns=[
        "createdAt",
        "domain",
        "shortCode",
        "shortUrl",
        "longUrl",
        "title",
        "tags",
        "visits",
    ],
)

# Exportar para CSV
df.to_csv("shlink_data.csv", index=False)

print("Arquivo CSV gerado com sucesso!")
