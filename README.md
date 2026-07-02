# Golden Barber SaaS 💈

O **Golden Barber** é um sistema SaaS (Software as a Service) completo para gestão de barbearias e salões, operando em uma arquitetura Multi-Tenant. Este projeto oferece um aplicativo para o cliente final agendar seus horários e um painel de administração (Dashboard) para o proprietário gerenciar serviços, profissionais e o calendário de sua empresa.

## 🚀 Arquitetura e Tecnologias

Este projeto foi construído separando as camadas de Frontend (Client) e Backend (API) para máxima escalabilidade:

### Backend (API REST)
* **Python 3.11+ & Django 5.x**
* **Django REST Framework (DRF)**: Criação de rotas da API.
* **SimpleJWT**: Sistema de Autenticação utilizando Tokens (Access/Refresh).
* **SQLite (Desenvolvimento)**: Banco de dados relacional.
* **Arquitetura Multi-Tenant**: Cada barbearia (Empresa) possui isolamento dos seus clientes, profissionais e agendamentos utilizando o mesmo banco de dados.
* **Signals**: Automação de notificações por E-mail diretamente via log (console backend) ao criar/atualizar agendamentos.

### Frontend (Interface Web)
* **React 18 & Vite**: Ambiente de desenvolvimento rápido e HMR.
* **Tailwind CSS v3**: Estilização baseada em utilitários adotando a filosofia **Dark Mode Premium** com tons escuros (backgrounds profundos) e destaques em Dourado (Gold).
* **Zustand**: Gerenciamento de estado global da aplicação.
* **Axios**: Cliente HTTP configurado com interceptors para injeção automática do Token JWT.
* **React Router Dom (planejado/escalonável)**: Gerenciamento de rotas e SPAs.

## 🛠 Funcionalidades Principais

1. **Autenticação Dupla**: O sistema comporta usuários tipo *Administradores*, *Profissionais (Barbeiros)* e *Clientes Finais*.
2. **Motor de Disponibilidade (Anti-Choque)**: Lógica nativa de calendário no backend que calcula precisamente os horários vagos com base no expediente da barbearia, bloqueando automaticamente sobreposições ou intervalos de almoço.
3. **Wizard de Agendamento (Frontend)**: Passo a passo para o cliente selecionar o Serviço, o Profissional e a Data/Hora ideal.
4. **Painel Administrativo (Dashboard)**: Tabela interativa para os profissionais/donos visualizarem compromissos filtrando por dia, profissional e status. Funções de aceitar ou rejeitar agendamentos.
5. **Painel do Cliente**: Acesso restrito via JWT onde o cliente final consegue ver seu histórico de marcações e efetuar cancelamentos. Os slots cancelados voltam automaticamente para a grade disponível.

## 💻 Como Rodar o Projeto

### Pré-requisitos
- Python 3.11 ou superior
- Node.js e NPM

### 1. Backend (Django)
```bash
# Entre na pasta raiz do projeto
cd SASS_BARBE_SHOP/backend

# (Opcional) Ative sua virtualenv e instale as dependências
pip install -r requirements.txt

# Execute as migrações do banco
python manage.py migrate

# Inicie o servidor Django (padrão porta 8000)
python manage.py runserver
```

### 2. Frontend (React)
```bash
# Entre na pasta do frontend
cd SASS_BARBE_SHOP/frontend

# Instale os pacotes NPM
npm install

# Inicie o servidor Vite
npm run dev
```

A aplicação frontend iniciará, conectando-se automaticamente ao backend em `http://127.0.0.1:8000/`.

---
*Desenvolvido por Luciano Saints para gestão de alto nível de Barbearias.*
