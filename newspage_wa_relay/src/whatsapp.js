const { create } = require('@open-wa/wa-automate');

let waClient = null;

async function initWhatsApp() {
    console.log("Initializing Open-WA...");
    waClient = await create({
        sessionId: "TELEGRAM_RELAY",
        multiDevice: true,
        authTimeout: 60,
        blockCrashLogs: true,
        disableSpins: true,
        headless: true,
        logConsole: false,
        popup: false,
        qrTimeout: 0, 
    });
    console.log("WhatsApp client initialized successfully!");
    return waClient;
}

async function sendImageToWA(base64Image, caption = "") {
    if (!waClient) {
        throw new Error("WhatsApp client not initialized yet.");
    }
    const targetId = process.env.TARGET_WA_ID;
    if (!targetId) {
        throw new Error("TARGET_WA_ID is not set in environment.");
    }
    
    const filename = `relay_${Date.now()}.jpg`;
    await waClient.sendImage(targetId, base64Image, filename, caption);
    console.log(`Image forwarded to ${targetId}`);
}

module.exports = {
    initWhatsApp,
    sendImageToWA
};
