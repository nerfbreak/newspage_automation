require('dotenv').config();
const { initWhatsApp } = require('./whatsapp');
const { initTelegramBot } = require('./telegram');

// Hugging Face Spaces requires binding to the PORT for health checks
const express = require('express');
const app = express();
const port = process.env.PORT || 7860;

app.get('/', (req, res) => {
    res.send('Telegram to WA Relay is running!');
});

async function main() {
    try {
        // Start express server for health check (needed by HF spaces)
        app.listen(port, () => {
            console.log(`Health check server listening on port ${port}`);
        });

        // 1. Init WA
        await initWhatsApp();
        
        // 2. Init Telegram
        initTelegramBot();
        
    } catch (error) {
        console.error("Critical failure during startup:", error);
        process.exit(1);
    }
}

main();
