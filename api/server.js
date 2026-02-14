const express = require('express');
const { google } = require('googleapis');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// --- CONFIGURACIÓN ---
// ID de la hoja de Google Sheets
const SPREADSHEET_ID = '1u8go_4XYqn_b0NmAGMiqmlJ07MoOtsINs5nlWeLPUnQ'; // Cambia por el ID de tu hoja
// Nombre de la hoja dentro de la hoja de cálculo
const SHEET_NAME = 'ACCESODEUSUARIOS'; // Cambia esto si es diferente

// Autenticación con la cuenta de servicio de Google
async function getAuthClient() {
  const auth = new google.auth.GoogleAuth({
    keyFile: 'credentials.json', // Este archivo no debe subirse a GitHub
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });
  return await auth.getClient();
}

// Ruta POST para consultar el código QR
app.post('/api/buscar-qr', async (req, res) => {
  const { codigo } = req.body;
  if (!codigo) {
    return res.status(400).json({ error: 'Falta el código QR' });
  }

  try {
    // Autenticación con la API de Google
    const auth = await getAuthClient();
    const sheets = google.sheets({ version: 'v4', auth });

    // Obtener los datos de la hoja de cálculo
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: SHEET_NAME,
    });

    const rows = response.data.values;
    if (!rows || rows.length === 0) {
      return res.status(404).json({ error: 'La hoja está vacía' });
    }

    // Buscar el índice de la columna "CODIGO"
    const headers = rows[0];
    const codigoIndex = headers.findIndex(h =>
      h.toString().trim().toUpperCase() === 'CODIGO' ||
      h.toString().trim().toUpperCase() === 'CÓDIGO'
    );

    if (codigoIndex === -1) {
      return res.status(500).json({
        error: 'No se encontró la columna CODIGO',
        headers: headers
      });
    }

    // Buscar el código dentro de las filas
    let filaEncontrada = null;
    for (let i = 1; i < rows.length; i++) {
      if (rows[i][codigoIndex] === codigo) {
        filaEncontrada = rows[i];
        break;
      }
    }

    if (!filaEncontrada) {
      return res.status(404).json({ error: 'Código no encontrado', codigo });
    }

    // Crear un objeto con los datos encontrados
    const registro = {};
    headers.forEach((header, idx) => {
      registro[header] = filaEncontrada[idx] || '';
    });

    res.json({ success: true, data: registro });

  } catch (error) {
    console.error('❌ ERROR DETALLADO EN BACKEND:', error); // Esto saldrá en tu terminal
    res.status(500).json({
      error: 'Error al consultar Google Sheets',
      detalle: error.message,
      respuesta: error.response?.data || null
    });
  }
});

// Exportar la función para que Vercel la reconozca como una función serverless
module.exports = app;
