import os
import gspread
import numpy as np
import cv2
from pyzbar.pyzbar import decode
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image

# Autenticación con Google Sheets
def authenticate_google_sheets():
    # Definir el alcance de los permisos necesarios para acceder a Sheets y Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('./credentials.json', scope)
    client = gspread.authorize(creds)
    return client

# Leer los datos de Google Sheets
def get_data_from_google_sheets(sheet_name):
    client = authenticate_google_sheets()
    
    # Abre la hoja de cálculo por su nombre
    sheet = client.open(sheet_name).sheet1  # Accede a la primera hoja
    # Obtén todos los valores de la hoja de cálculo
    data = sheet.get_all_records()
    
    return data

# Función para leer QR desde la cámara en tiempo real
def read_qr_from_camera():
    """Lee un código QR desde la cámara en tiempo real"""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("No se pudo acceder a la cámara.")
        return None

    while True:
        ret, frame = cap.read()

        if not ret:
            print("No se pudo obtener la imagen de la cámara.")
            continue

        decoded_objects = decode(frame)

        for obj in decoded_objects:
            points = obj.polygon
            if len(points) == 4:
                pts = [tuple(point) for point in points]
                pts = np.array(pts, dtype=np.int32)
                cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            else:
                cv2.circle(frame, (obj.rect.left, obj.rect.top), 5, (0, 0, 255), -1)

            qr_data = obj.data.decode("utf-8")

            cv2.putText(frame, qr_data, (obj.rect.left, obj.rect.top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            cv2.imshow("QR Scanner", frame)
            if qr_data:
                cap.release()
                cv2.destroyAllWindows()
                return qr_data

        cv2.imshow("QR Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

# Buscar los datos en Google Sheets basados en el QR
def search_google_sheets_data(qr_value):
    sheet_name = 'ACCESODEUSUARIOS'  # Nombre de la hoja en Google Sheets
    data = get_data_from_google_sheets(sheet_name)

    found = False
    for row in data:
        if row['CODIGO'] == qr_value:  # Asegúrate de que la columna 'CODIGO' existe en el archivo
            print("\n" + "="*50)
            print("INFORMACIÓN ENCONTRADA:")
            print("="*50)

            # Mostrar todos los datos de la fila
            columns = ["CODIGO", "NOMBRE", "PLACA", "NUMERO DE CONTACTO", "ULTIMO PAGO","QR", "RECIBO"]
            for col_name in columns:
                print(f"{col_name}: {row.get(col_name, 'No disponible')}")

            print("="*50)
            found = True
            break

    if not found:
        print(f"\n❌ No se encontró el código '{qr_value}' en Google Sheets")
        
        # Mostrar algunos códigos disponibles para ayudar
        print("\nCódigos disponibles (primeros 10):")
        available_codes = [row['CODIGO'] for row in data][:10]
        for code in available_codes:
            print(f"  - {code}")

def main():
    print("=== Sistema de Consulta por Código QR ===\n")

    print("1. Leyendo código QR desde la cámara...")
    qr_value = read_qr_from_camera()
    if not qr_value:
        print("No se pudo leer el código QR.")
        return
    
    print(f"✓ Código QR leído: {qr_value}\n")
    
    print("2. Buscando coincidencia en el archivo Google Sheets...")
    search_google_sheets_data(qr_value)

if __name__ == "__main__":
    main()