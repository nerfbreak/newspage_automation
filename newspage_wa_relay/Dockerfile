FROM node:20-bullseye-slim

# Install Chromium and other dependencies for open-wa
RUN apt-get update && apt-get install -y \
    chromium \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for puppeteer/open-wa to use the installed Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Hugging Face Spaces requires running as a non-root user (id 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user package*.json ./
RUN npm install

COPY --chown=user . .

# Create the data directory for open-wa session and set permissions
RUN mkdir -p .data && chown -R user:user .data

EXPOSE 7860
ENV PORT=7860

CMD ["npm", "start"]
