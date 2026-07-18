# Fase de Build (Node.js)
FROM node:20-alpine AS build

WORKDIR /app

# Copia os arquivos de dependência e instala
COPY package.json package-lock.json* ./
RUN npm install

# Copia o restante do código
COPY . .

# Argumento para URL da API (usado na hora do build se não usarmos proxy, mas com proxy podemos ignorar)
ENV VITE_API_URL=/

# Compila a aplicação React/Vite
RUN npm run build

# Fase de Servir (Nginx)
FROM nginx:alpine

# Remove configuração default do nginx
RUN rm /etc/nginx/conf.d/default.conf

# Altera o user do Nginx para que consiga ler arquivos do volume compartilhado com o Django
RUN sed -i 's/user  nginx;/user  root;/' /etc/nginx/nginx.conf

# Copia a configuração customizada
COPY nginx.conf /etc/nginx/conf.d/

# Copia os arquivos buildados da fase anterior
COPY --from=build /app/dist /usr/share/nginx/html

# Cria o ponto de montagem para o volume de media compartilhado
RUN mkdir -p /app/media/profissionais && chmod -R 755 /app/media

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
