FROM node:20-alpine

WORKDIR /app

# Install system dependencies for Playwright
RUN apk update && \
    apk add --no-cache \
    chromium \
    ffmpeg \
    font-noto \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    bash \
    libc6-compat \
    libstdc++ \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    wget \
    xvfb \
    dbus \
    gtk+3.0

# Set browser path for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV CHROMIUM_PATH=/usr/bin/chromium-browser

# Copy package.json
COPY package.json ./

# Install dependencies
RUN npm install

# Install Playwright with system browser
RUN npx playwright install --with-deps chromium

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 3000

# Command to run the application
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0", "-p", "3000"]
