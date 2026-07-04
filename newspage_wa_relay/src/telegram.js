const { Telegraf } = require('telegraf');
const { downloadImageAsBase64 } = require('./utils');
const { sendImageToWA } = require('./whatsapp');

let bot = null;

function initTelegramBot() {
    const token = process.env.TELEGRAM_BOT_TOKEN;
    if (!token) {
        throw new Error("TELEGRAM_BOT_TOKEN is not set in environment.");
    }

    bot = new Telegraf(token);

    // US1: Handle incoming photos
    bot.on('photo', async (ctx) => {
        try {
            console.log("Received a photo from Telegram.");
            const photos = ctx.message.photo;
            // Get the highest resolution photo (last in the array)
            const highestRes = photos[photos.length - 1];
            
            // Get file URL from Telegram
            const fileUrl = await ctx.telegram.getFileLink(highestRes.file_id);
            
            // Download as Base64 Data URI
            const base64Image = await downloadImageAsBase64(fileUrl.href);
            
            // Get caption if available
            const caption = ctx.message.caption || "";
            
            // Send to WA
            await sendImageToWA(base64Image, caption);
            
            // Acknowledge back to user
            ctx.reply("Image successfully forwarded to WhatsApp.");
        } catch (error) {
            console.error("Error processing photo:", error);
            ctx.reply("Failed to forward image to WhatsApp.");
        }
    });

    // US2: Ignore non-image messages
    bot.on('text', (ctx) => {
        console.log("Ignored text message.");
        ctx.reply("This bot only accepts images. Text messages are ignored.");
    });
    
    bot.on('document', (ctx) => {
        console.log("Ignored document.");
        ctx.reply("This bot only accepts compressed images (not sent as file).");
    });

    bot.launch();
    console.log("Telegram bot initialized and polling...");
    
    // Enable graceful stop
    process.once('SIGINT', () => bot.stop('SIGINT'));
    process.once('SIGTERM', () => bot.stop('SIGTERM'));
}

module.exports = {
    initTelegramBot
};
