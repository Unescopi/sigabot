FROM node:16-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ENV PORT=80

EXPOSE 80

CMD ["node", "app.js"] 