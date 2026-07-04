const axios = require('axios');

async function downloadImageAsBase64(url) {
    const response = await axios.get(url, { responseType: 'arraybuffer' });
    const buffer = Buffer.from(response.data, 'binary');
    const mimeType = response.headers['content-type'];
    return `data:${mimeType};base64,${buffer.toString('base64')}`;
}

module.exports = {
    downloadImageAsBase64
};
