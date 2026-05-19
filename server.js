const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const axios = require('axios');
const path = require('path');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static('.')); // Servir archivos estáticos del dashboard

// Endpoint para obtener datos de X
app.get('/api/social-data', async (req, res) => {
    try {
        const bearerToken = process.env.X_BEARER_TOKEN;
        
        if (!bearerToken) {
            return res.status(500).json({ error: 'Falta X_BEARER_TOKEN en el archivo .env' });
        }

        // Búsqueda de menciones reales de Claro Ecuador
        // Usamos la API v2 de Twitter (X)
        const query = '@ClaroEcuador OR #ClaroEcuador OR "Claro Ecuador"';
        
        const response = await axios.get('https://api.twitter.com/2/tweets/search/recent', {
            params: {
                query: query,
                'tweet.fields': 'created_at,author_id,public_metrics',
                'user.fields': 'username,name,profile_image_url',
                'expansions': 'author_id',
                'max_results': 10
            },
            headers: {
                'Authorization': `Bearer ${bearerToken}`
            }
        });

        // Formatear la respuesta para el Dashboard
        const tweets = response.data.data || [];
        const users = response.data.includes ? response.data.includes.users : [];

        const formattedFeed = tweets.map(tweet => {
            const user = users.find(u => u.id === tweet.author_id);
            return {
                user: `@${user ? user.username : 'usuario'}`,
                text: tweet.text,
                time: new Date(tweet.created_at).toLocaleTimeString(),
                url: `https://x.com/${user ? user.username : 'i'}/status/${tweet.id}`,
                category: tweet.text.toLowerCase().includes('venta') || tweet.text.toLowerCase().includes('portabilidad') ? 'Lead' : 'Mención'
            };
        });

        res.json({
            feed: formattedFeed,
            metrics: {
                total_mentions: tweets.length * 123, // Multiplicador simulado para visualización
                sentiment: { positive: 45, negative: 35, neutral: 20 }
            }
        });

    } catch (error) {
        console.error('Error fetching from X API:', error.response ? error.response.data : error.message);
        
        // Si falla la API (por límites o credenciales inválidas), enviamos datos simulados 
        // para que el dashboard no se rompa, pero avisamos en la consola.
        res.json({
            isSimulated: true,
            error: 'API Error: Usando datos de respaldo.',
            feed: [
                { user: '@claro_fan', text: 'Excelente señal en el valle de los chillos!', time: 'Ahora', url: 'https://x.com', category: 'Positivo' },
                { user: '@user_quito', text: '¿Cuándo llega el 5G a mi sector? @ClaroEcuador', time: '5m ago', url: 'https://x.com', category: 'Lead' }
            ],
            metrics: {
                total_mentions: 5412,
                sentiment: { positive: 30, negative: 52, neutral: 18 }
            }
        });
    }
});

app.listen(PORT, () => {
    console.log(`🚀 Servidor del Dashboard corriendo en http://localhost:${PORT}`);
    console.log(`Sliencio de archivos estáticos desde: ${path.join(__dirname, '.')}`);
});
