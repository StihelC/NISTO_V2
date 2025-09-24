FROM node:22-alpine

WORKDIR /srv/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend .

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

