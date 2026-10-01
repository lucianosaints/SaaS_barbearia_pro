# Ajuste proposto para o build do frontend

Proposta local para revisão; ainda não aplicada ao servidor. A referência recebida está em `references/frontend.Dockerfile.production`.

No Dockerfile de produção, substituir:

```dockerfile
FROM node:20-alpine AS build
```

por:

```dockerfile
FROM node:22-alpine AS build
```

E substituir:

```dockerfile
COPY package.json package-lock.json* ./
RUN npm install
```

por:

```dockerfile
COPY package.json package-lock.json ./
RUN npm ci
```

Isso acompanha o requisito local de Node >=22.12.0 e usa as versões fixadas pelo lockfile. O package.json e o package-lock.json da versão atualizada devem ser enviados juntos.

O restante do Dockerfile depende do nginx.conf e dos volumes de produção. Conferir esses arquivos e o backend antes de montar/publicar uma imagem. O uso de root no Nginx foi explicado no arquivo existente como necessário para ler mídia compartilhada; revisar as permissões antes de modificar essa parte. Ainda não foi executado build Docker dessa proposta.
