# Sistema de Chamada SUS

Sistema de gerenciamento de filas integrado ao e-SUS para unidades de saúde.

## 📋 Funcionalidades

- **Geração de senhas**: Senhas automáticas com prefixo para prioridade (P) e normal (A)
- **Exibição em painéis**: Nome/iniciais do paciente, sala, histórico das últimas 4 chamadas
- **Notificação sonora**: Som de alerta quando paciente é chamado
- **Atualização em tempo real**: WebSocket para atualizações instantâneas (≤1s)
- **Filas por sala/setor**: Organização independente de filas
- **Modo offline**: Cadastro manual quando e-SUS não está disponível
- **Prioridade legal**: Conforme Lei 10.048/2000 (idosos, gestantes, PcD, etc.)
- **Painéis independentes**: Cada sala tem seu próprio painel de chamadas
- **Relatórios**: Resumo diário, ausências, performance por sala
- **Registro de ausência**: Controle de pacientes que não compareceram
- **Integração e-SUS**: Busca de pacientes via API (≤3s timeout)

## 🚀 Instalação

### Requisitos

- Python 3.10+
- pip

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/BiancaMR04/Sistema-de-Chamada-SUS.git
cd Sistema-de-Chamada-SUS
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente (opcional):
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. Execute a aplicação:
```bash
python run.py
```

5. Acesse em: http://localhost:5000

## 📁 Estrutura do Projeto

```
Sistema-de-Chamada-SUS/
├── app/
│   ├── __init__.py          # Factory da aplicação Flask
│   ├── models/              # Modelos do banco de dados
│   │   ├── __init__.py
│   │   └── models.py        # Patient, Room, QueueEntry, etc.
│   ├── routes/              # Rotas da API e páginas
│   │   ├── __init__.py
│   │   ├── main.py          # Páginas principais
│   │   ├── api.py           # API REST
│   │   └── admin.py         # Páginas administrativas
│   ├── services/            # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── queue_service.py # Gerenciamento de filas
│   │   ├── esus_service.py  # Integração e-SUS
│   │   └── report_service.py# Geração de relatórios
│   ├── static/              # Arquivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── audio/
│   └── templates/           # Templates HTML
├── tests/                   # Testes automatizados
├── config.py                # Configurações
├── run.py                   # Ponto de entrada
└── requirements.txt         # Dependências
```

## 🔌 API Endpoints

### Pacientes
- `GET /api/patients` - Listar pacientes
- `GET /api/patients/search?cpf=&name=` - Buscar paciente
- `POST /api/patients/offline` - Cadastrar paciente (modo offline)
- `PUT /api/patients/<id>/priority` - Atualizar prioridade

### Salas
- `GET /api/rooms` - Listar salas
- `POST /api/rooms` - Criar sala
- `PUT /api/rooms/<id>` - Atualizar sala

### Fila
- `GET /api/queue/<room_id>` - Ver fila de uma sala
- `POST /api/queue/<room_id>/add` - Adicionar à fila
- `POST /api/queue/call/next/<room_id>` - Chamar próximo
- `POST /api/queue/call/<entry_id>` - Chamar paciente específico
- `POST /api/queue/recall/<entry_id>` - Chamar novamente
- `POST /api/queue/attend/<entry_id>` - Marcar atendido
- `POST /api/queue/absent/<entry_id>` - Marcar ausente
- `POST /api/queue/cancel/<entry_id>` - Cancelar senha

### Display
- `GET /api/display/<room_id>` - Dados para painel

### Relatórios
- `GET /api/reports/daily` - Resumo diário
- `GET /api/reports/absences` - Relatório de ausências
- `GET /api/reports/room/<id>/performance` - Performance da sala
- `GET /api/reports/hourly` - Distribuição por hora

### e-SUS
- `GET /api/esus/status` - Status da conexão
- `GET /api/esus/search?cpf=&cns=` - Buscar no e-SUS

## ⚖️ Prioridades (Lei 10.048/2000)

| Prioridade | Descrição | Peso |
|------------|-----------|------|
| IDOSO_80 | Idosos 80+ (Super Prioridade) | 100 |
| AUTISTA | Pessoa com TEA | 90 |
| DEFICIENTE | Pessoa com Deficiência | 80 |
| IDOSO_60 | Idosos 60+ | 70 |
| GESTANTE | Gestantes | 60 |
| LACTANTE | Lactantes | 50 |
| CRIANCA | Crianças com responsável | 40 |
| NORMAL | Atendimento normal | 0 |

## 🧪 Testes

```bash
python -m pytest tests/ -v
```

## 📊 Requisitos de Performance

- Disponibilidade: 99%
- Atualização em tempo real: ≤1s
- Resposta API e-SUS: ≤3s
- Interface acessível e fácil de usar

## 📸 Screenshots

### Página Inicial
![Home](https://github.com/user-attachments/assets/ce38c599-d931-4af6-ab67-9f1efa9a5d7c)

### Gerenciamento de Salas
![Rooms](https://github.com/user-attachments/assets/7fa4b2c2-09c1-44c1-90c1-5a439746b185)

### Recepção
![Reception](https://github.com/user-attachments/assets/351071cc-8633-4701-9689-b287f46a6b2d)

### Painel de Chamadas
![Panel](https://github.com/user-attachments/assets/10f7fefa-c46c-4cda-8db8-7863a8fd345b)

## 📝 Licença

Este projeto é licenciado sob a MIT License.