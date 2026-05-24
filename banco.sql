-- ==========================================
-- 1. ATUALIZAÇÃO DA TABELA USUÁRIOS (EVITA ERROS SE ELA JÁ EXISTE)
-- ==========================================
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) DEFAULT 'comprador';
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pendente';
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS carteira_saldo DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS carteira_bloqueado DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS asaas_customer_id VARCHAR(100);

-- ==========================================
-- 2. CRIAÇÃO DAS TABELAS (ESTRUTURA)
-- ==========================================
CREATE TABLE IF NOT EXISTS usuarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  senha VARCHAR(255) NOT NULL,
  aldeia VARCHAR(100),
  etnia VARCHAR(100),
  is_admin BOOLEAN DEFAULT FALSE,
  tipo VARCHAR(20) DEFAULT 'comprador', -- 'comprador' ou 'vendedor'
  status VARCHAR(20) DEFAULT 'pendente', -- 'pendente', 'aprovado', 'rejeitado'
  carteira_saldo DECIMAL(10,2) DEFAULT 0.00,
  carteira_bloqueado DECIMAL(10,2) DEFAULT 0.00,
  asaas_customer_id VARCHAR(100),
  criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categorias (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS artesanatos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo VARCHAR(150) NOT NULL,
  descricao TEXT,
  preco DECIMAL(10,2),
  categoria_id INT REFERENCES categorias(id),
  usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
  aldeia VARCHAR(100),
  disponivel BOOLEAN DEFAULT TRUE,
  imagem_url VARCHAR(500),
  criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compras (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  artesanato_id UUID REFERENCES artesanatos(id),
  comprador_id UUID REFERENCES usuarios(id),
  vendedor_id UUID REFERENCES usuarios(id),
  valor DECIMAL(10,2) NOT NULL,
  status VARCHAR(50) DEFAULT 'aguardando_pagamento',
  asaas_payment_id VARCHAR(100),
  endereco_entrega TEXT,
  valor_frete DECIMAL(10,2) DEFAULT 0.00,
  criado_em TIMESTAMP DEFAULT NOW()
);

-- Adiciona caso a tabela compras já tenha sido criada antes
ALTER TABLE compras ADD COLUMN IF NOT EXISTS endereco_entrega TEXT;
ALTER TABLE compras ADD COLUMN IF NOT EXISTS valor_frete DECIMAL(10,2) DEFAULT 0.00;

CREATE TABLE IF NOT EXISTS eventos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo VARCHAR(150) NOT NULL,
  descricao TEXT,
  data_evento DATE,
  local VARCHAR(150),
  usuario_id UUID REFERENCES usuarios(id),
  imagem_url VARCHAR(500),
  criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interesses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
  artesanato_id UUID REFERENCES artesanatos(id) ON DELETE CASCADE,
  criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comentarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conteudo TEXT NOT NULL,
  usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
  artesanato_id UUID REFERENCES artesanatos(id) ON DELETE CASCADE,
  criado_em TIMESTAMP DEFAULT NOW()
);

-- ==========================================
-- 2. DESATIVAR RLS (SEGURANÇA)
-- ==========================================
ALTER TABLE usuarios DISABLE ROW LEVEL SECURITY;
ALTER TABLE categorias DISABLE ROW LEVEL SECURITY;
ALTER TABLE artesanatos DISABLE ROW LEVEL SECURITY;
ALTER TABLE eventos DISABLE ROW LEVEL SECURITY;
ALTER TABLE interesses DISABLE ROW LEVEL SECURITY;
ALTER TABLE comentarios DISABLE ROW LEVEL SECURITY;
ALTER TABLE compras DISABLE ROW LEVEL SECURITY;

NOTIFY pgrst, 'reload schema';

-- ==========================================
-- 3. INSERIR DADOS PADRÃO E APROVAÇÃO
-- ==========================================
INSERT INTO categorias (nome) 
SELECT nome FROM (VALUES 
  ('Cestaria'), ('Cerâmica'), ('Colares'),
  ('Pinturas'), ('Esculturas'), ('Tecidos')
) AS v(nome)
WHERE NOT EXISTS (SELECT 1 FROM categorias WHERE categorias.nome = v.nome);

-- Admin (já aprovado)
INSERT INTO usuarios (nome, email, senha, aldeia, etnia, is_admin, tipo, status)
SELECT 'Aruanã Karajá', 'usuario@indigena.com', '$2b$12$d7a8xbaeo4Qc2B4SSY4Mb.jsxPb4uoVV/frj2Oz0lq7LdAsES0bNK', 'Santa Isabel do Morro', 'Karajá', TRUE, 'vendedor', 'aprovado'
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'usuario@indigena.com');

-- Vendedor e Comprador
INSERT INTO usuarios (nome, email, senha, aldeia, etnia, is_admin, tipo, status)
SELECT 'Maiara Krahô', 'visitante@indigena.com', '$2b$12$d7a8xbaeo4Qc2B4SSY4Mb.jsxPb4uoVV/frj2Oz0lq7LdAsES0bNK', 'Pedra Branca', 'Krahô', FALSE, 'comprador', 'aprovado'
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'visitante@indigena.com');

-- Atualiza todos os usuários existentes para aprovados para não quebrar o sistema atual
UPDATE usuarios SET status = 'aprovado' WHERE status = 'pendente';
UPDATE usuarios SET tipo = 'vendedor' WHERE is_admin = TRUE;
