Cultura Viva do Tocantins
Plataforma de valorização, divulgação e comercialização do artesanato indígena do Tocantins.

Badges:
https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white  
https://img.shields.io/badge/Flask-Framework-black?logo=flask  
https://img.shields.io/badge/Supabase-Database-3ECF8E?logo=supabase&logoColor=white  
https://img.shields.io/badge/Asaas-Pagamentos-FF6F00  
https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow  
https://img.shields.io/badge/GitHub-Reposit%C3%B3rio-181717?logo=github

Descrição do Projeto:
O Cultura Viva do Tocantins é um sistema web criado para promover o artesanato indígena, facilitar a comercialização de produtos culturais e divulgar eventos tradicionais da região.

Segundo o documento do projeto:

“O sistema foi desenvolvido para funcionar como uma plataforma de artesanato indígena, permitindo cadastro de vendedores e compradores, publicação de artesanatos, realização de compras online, pagamentos via PIX, gerenciamento de eventos culturais e administração da plataforma.”

A plataforma também conta com uma área administrativa para aprovação de vendedores e controle geral do sistema.

Tecnologias Utilizadas:
Python

Flask

Supabase (banco de dados)

Asaas (pagamentos via PIX)

HTML, CSS e JavaScript

bcrypt (criptografia)

python-dotenv (variáveis de ambiente)

Arquivos importantes:

app.py — rotas, autenticação, compras, pagamentos, administração

.env — chaves e credenciais

requirements.txt — dependências

banco.sql — estrutura do banco

atualizacao.sql — atualizações do banco

 Como Executar o Sistema Localmente:
1. Clonar o repositório
Código
git clone https://github.com/seu-usuario/cultura-viva-tocantins.git
cd cultura-viva-tocantins
2. Criar e ativar o ambiente virtual
Linux/Mac:

Código
python3 -m venv venv
source venv/bin/activate
Windows:

Código
python -m venv venv
venv\Scripts\activate
3. Instalar dependências
Código
pip install -r requirements.txt
4. Criar o arquivo .env
Código
SUPABASE_URL=
SUPABASE_KEY=
ASAAS_API_KEY=
SECRET_KEY=
5. Executar o sistema:
Código
python app.py
Acesse no navegador:
http://localhost:5000

 Funcionalidades Implementadas:
Cadastro de usuários

Login de usuários

Cadastro de artesanatos

Sistema de compras

Pagamento via PIX

Aprovação de vendedores

Área administrativa

Comentários e interesses

Cadastro de eventos culturais

Protótipo de baixa fidelidade

Fluxo de navegação intuitivo

 Principais Telas:
Home

Login

Cadastro

Perfil do Usuário

Lista de Artesanatos

Detalhes do Produto

Checkout

Pagamento PIX

Tela de Eventos

Painel Administrativo

 Integrantes do Grupo:
Maria Mikaelle Martins Rezendes

Adenilson José Lima dos Santos

Iara Herude Alves Pereira Javaé

Koroxia Tubehele Javaé

Paulo Vitor Alves da Conceição

Objetivo Geral
“O sistema proposto busca valorizar o artesanato indígena, facilitar a comercialização dos produtos e promover eventos culturais, utilizando uma plataforma digital moderna e acessível.”
