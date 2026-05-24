import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session
from supabase import create_client, Client
from dotenv import load_dotenv
import bcrypt
from functools import wraps
from datetime import datetime
import uuid

# 1. Carregar .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")
app.config['SESSION_TYPE'] = 'filesystem'

# 2. Conectar ao Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key) if url and key else None

# Chave e URL do Asaas
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")
default_url = "https://sandbox.asaas.com/api/v3"
if ASAAS_API_KEY and (ASAAS_API_KEY.startswith("$aae") or ASAAS_API_KEY.startswith("$aact_prod_")):
    default_url = "https://api.asaas.com/v3"
ASAAS_API_URL = os.getenv("ASAAS_API_URL", default_url).rstrip('/')

# 4. Decorator @login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 5. Decorator @admin_required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 6. Criar admin automaticamente
def create_admin():
    if not supabase: return
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_senha = os.getenv("ADMIN_SENHA")
    
    if not admin_email or not admin_senha:
        return

    res = supabase.table("usuarios").select("*").eq("email", admin_email).execute()
    if not res.data:
        hashed = bcrypt.hashpw(admin_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        supabase.table("usuarios").insert({
            "nome": "Administrador",
            "email": admin_email,
            "senha": hashed,
            "is_admin": True,
            "tipo": "vendedor",
            "status": "aprovado",
            "aldeia": "Tocantins",
            "etnia": "Sistema"
        }).execute()

def seed_categories():
    if not supabase: return
    res = supabase.table("categorias").select("id").limit(1).execute()
    if not res.data:
        categorias = [
            {"nome": "Cestaria"},
            {"nome": "Cerâmica"},
            {"nome": "Colares"},
            {"nome": "Pinturas"},
            {"nome": "Esculturas"},
            {"nome": "Tecidos"}
        ]
        supabase.table("categorias").insert(categorias).execute()
        print("Categorias semeadas com sucesso!")

# --- ROTAS PRINCIPAIS ---

@app.route('/')
def index():
    artesanatos = []
    if supabase:
        try:
            res = supabase.table("artesanatos").select("*, categorias(nome)").order("criado_em", desc=True).limit(6).execute()
            artesanatos = res.data
        except Exception as e:
            print(f"Erro Supabase: {e}")
    return render_template('index.html', artesanatos=artesanatos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        res = supabase.table("usuarios").select("*").eq("email", email).execute()
        if res.data:
            user = res.data[0]
            if bcrypt.checkpw(senha.encode('utf-8'), user['senha'].encode('utf-8')):
                if user['status'] != 'aprovado':
                    flash("Sua conta ainda está em análise pelo administrador. Aguarde a aprovação.", "warning")
                    return redirect(url_for('login'))

                session['user_id'] = user['id']
                session['nome'] = user['nome']
                session['email'] = user['email']
                session['is_admin'] = user['is_admin']
                session['tipo'] = user['tipo']
                flash(f"Bem-vindo(a), {user['nome']}!", "success")
                return redirect(url_for('index'))
        
        flash("Email ou senha inválidos.", "danger")
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        tipo = request.form.get('tipo', 'comprador') # comprador ou vendedor
        aldeia = request.form.get('aldeia') if tipo == 'vendedor' else None
        etnia = request.form.get('etnia') if tipo == 'vendedor' else None
        
        hashed = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            status = 'aprovado' if tipo == 'comprador' else 'pendente'
            supabase.table("usuarios").insert({
                "nome": nome,
                "email": email,
                "senha": hashed,
                "aldeia": aldeia,
                "etnia": etnia,
                "tipo": tipo,
                "status": status
            }).execute()
            
            if status == 'aprovado':
                flash("Cadastro realizado com sucesso! Você já pode fazer login.", "success")
            else:
                flash("Cadastro de Vendedor realizado! Sua conta passará por uma análise antes da liberação.", "info")
                
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Erro ao cadastrar: Email já existe ou dados inválidos.", "danger")
            
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sessão encerrada.", "info")
    return redirect(url_for('index'))

@app.route('/perfil')
@login_required
def perfil():
    user_res = supabase.table("usuarios").select("*").eq("id", session['user_id']).execute()
    if not user_res.data:
        session.clear()
        flash("Seu usuário não foi encontrado no banco de dados. Faça login novamente.", "warning")
        return redirect(url_for('login'))
        
    user = user_res.data[0]
    
    meus_artesanatos = []
    minhas_compras = []
    minhas_vendas = []
    
    if user['tipo'] == 'vendedor' or user['is_admin']:
        meus_artesanatos = supabase.table("artesanatos").select("*, categorias(nome)").eq("usuario_id", session['user_id']).execute().data
        minhas_vendas = supabase.table("compras").select("*, artesanatos(titulo, imagem_url), usuarios!comprador_id(nome)").eq("vendedor_id", session['user_id']).order("criado_em", desc=True).execute().data
    
    if user['tipo'] == 'comprador' or user['is_admin']:
        minhas_compras = supabase.table("compras").select("*, artesanatos(titulo, imagem_url), usuarios!vendedor_id(nome)").eq("comprador_id", session['user_id']).order("criado_em", desc=True).execute().data
        
    return render_template('perfil.html', user=user, artesanatos=meus_artesanatos, compras=minhas_compras, vendas=minhas_vendas)

@app.route('/perfil/editar', methods=['POST'])
@login_required
def editar_perfil():
    nome = request.form.get('nome')
    
    update_data = {"nome": nome}
    if session.get('tipo') == 'vendedor':
        update_data["aldeia"] = request.form.get('aldeia')
        update_data["etnia"] = request.form.get('etnia')
        
    supabase.table("usuarios").update(update_data).eq("id", session['user_id']).execute()
    
    session['nome'] = nome
    flash("Perfil atualizado!", "success")
    return redirect(url_for('perfil'))

# --- SISTEMA DE ADMIN E APROVAÇÃO ---

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Exibe todos os usuários normais (vendedores e consumidores/compradores), ocultando as contas de administradores.
    usuarios = supabase.table("usuarios").select("*").eq("is_admin", False).order("criado_em").execute().data
    
    # Todos os produtos da plataforma para controle administrativo
    artesanatos_raw = supabase.table("artesanatos").select("*, categorias(nome)").order("criado_em").execute().data
    
    # Todas as compras para controle financeiro
    compras_raw = supabase.table("compras").select("*, artesanatos(titulo)").order("criado_em").execute().data
    
    # Mapeamento robusto de IDs para Nomes de usuários (evita erros de relacionamentos complexos no Supabase)
    todos_usuarios = supabase.table("usuarios").select("id, nome").execute().data
    user_map = {u['id']: u['nome'] for u in todos_usuarios}
    
    artesanatos = []
    for art in artesanatos_raw:
        art['vendedor_nome'] = user_map.get(art['usuario_id'], 'Desconhecido')
        artesanatos.append(art)
        
    compras = []
    total_bloqueado = 0.0
    total_liberado = 0.0
    
    for c in compras_raw:
        c['comprador_nome'] = user_map.get(c['comprador_id'], 'Desconhecido')
        c['vendedor_nome'] = user_map.get(c['vendedor_id'], 'Desconhecido')
        compras.append(c)
        
        # Calcular estatísticas financeiras
        valor_total = float(c['valor'] or 0) + float(c['valor_frete'] or 0)
        if c['status'] in ['pago', 'despachado']:
            total_bloqueado += valor_total
        elif c['status'] == 'entregue':
            total_liberado += valor_total
            
    # Contadores
    total_u = len(usuarios)
    total_a = len(artesanatos)
    total_e = len(supabase.table("eventos").select("id").execute().data)
    total_c = len(supabase.table("comentarios").select("id").execute().data)

    return render_template('admin/dashboard.html', 
                           usuarios=usuarios, 
                           compras=compras, 
                           artesanatos=artesanatos,
                           total_u=total_u, 
                           total_a=total_a, 
                           total_e=total_e, 
                           total_c=total_c,
                           total_bloqueado=total_bloqueado,
                           total_liberado=total_liberado)

@app.route('/admin/aprovar/<id>', methods=['POST'])
@admin_required
def aprovar_usuario(id):
    supabase.table("usuarios").update({"status": "aprovado"}).eq("id", id).execute()
    flash("Usuário aprovado com sucesso!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/rejeitar/<id>', methods=['POST'])
@admin_required
def rejeitar_usuario(id):
    supabase.table("usuarios").update({"status": "rejeitado"}).eq("id", id).execute()
    flash("Usuário rejeitado.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/deletar_usuario/<id>', methods=['POST'])
@admin_required
def deletar_usuario(id):
    supabase.table("usuarios").delete().eq("id", id).execute()
    flash("Usuário removido com sucesso.", "success")
    return redirect(url_for('admin_dashboard'))

# --- FLUXO DE COMPRA (ESCROW) ---

@app.route('/checkout/<artesanato_id>')
@login_required
def checkout(artesanato_id):
    if session.get('tipo') != 'comprador':
        flash("Apenas contas de Comprador podem realizar compras.", "warning")
        return redirect(url_for('detalhe_artesanato', id=artesanato_id))
        
    art_res = supabase.table("artesanatos").select("*, usuarios(nome)").eq("id", artesanato_id).execute()
    if not art_res.data or not art_res.data[0]['disponivel']:
        flash("Produto indisponível.", "danger")
        return redirect(url_for('listar_artesanatos'))
        
    return render_template('checkout.html', artesanato=art_res.data[0])

@app.route('/comprar/<artesanato_id>', methods=['POST'])
@login_required
def comprar(artesanato_id):
    if session.get('tipo') != 'comprador':
        flash("Apenas contas de Comprador podem realizar compras.", "warning")
        return redirect(url_for('detalhe_artesanato', id=artesanato_id))
        
    art_res = supabase.table("artesanatos").select("*").eq("id", artesanato_id).execute()
    if not art_res.data or not art_res.data[0]['disponivel']:
        flash("Produto indisponível.", "danger")
        return redirect(url_for('listar_artesanatos'))
        
    art = art_res.data[0]
    
    endereco = request.form.get('endereco_completo')
    frete_str = request.form.get('valor_frete', '0')
    try:
        valor_frete = float(frete_str)
    except:
        valor_frete = 0.0

    cpf = request.form.get('cpf', '').replace('.', '').replace('-', '')
    
    # Criar registro de compra pendente
    res = supabase.table("compras").insert({
        "artesanato_id": art['id'],
        "comprador_id": session['user_id'],
        "vendedor_id": art['usuario_id'],
        "valor": art['preco'],
        "valor_frete": valor_frete,
        "endereco_entrega": endereco,
        "status": "aguardando_pagamento"
    }).execute()
    
    compra_id = res.data[0]['id']
    
    # -------------------------------------------------------------
    # INTEGRAÇÃO REAL COM ASAAS
    # -------------------------------------------------------------
    if ASAAS_API_KEY:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "access_token": ASAAS_API_KEY
        }
        
        # 1. Recuperar ou Criar Cliente no Asaas
        user_db = supabase.table("usuarios").select("asaas_customer_id").eq("id", session['user_id']).execute()
        customer_id = user_db.data[0]['asaas_customer_id'] if user_db.data else None
        
        if not customer_id:
            customer_payload = {
                "name": session['nome'],
                "email": session['email'],
                "cpfCnpj": cpf
            }
            cust_req = requests.post(f"{ASAAS_API_URL}/customers", json=customer_payload, headers=headers)
            if cust_req.status_code == 200:
                customer_id = cust_req.json().get('id')
                supabase.table("usuarios").update({"asaas_customer_id": customer_id}).eq("id", session['user_id']).execute()
            else:
                print("ERRO ASAAS CUSTOMER:", cust_req.text)
                
        # 2. Gerar a Cobrança PIX
        if customer_id:
            valor_total = float(art['preco']) + valor_frete
            hoje = datetime.now()
            vencimento = f"{hoje.year}-{hoje.month:02d}-{(hoje.day+1):02d}" # Vence amanhã
            
            payment_payload = {
                "customer": customer_id,
                "billingType": "PIX",
                "dueDate": vencimento,
                "value": round(valor_total, 2),
                "description": f"Compra de Artesanato: {art['titulo']} + Frete",
                "externalReference": compra_id
            }
            pay_req = requests.post(f"{ASAAS_API_URL}/payments", json=payment_payload, headers=headers)
            if pay_req.status_code == 200:
                asaas_payment_id = pay_req.json().get('id')
                supabase.table("compras").update({"asaas_payment_id": asaas_payment_id}).eq("id", compra_id).execute()
            else:
                print("ERRO ASAAS PAYMENT:", pay_req.text)

    flash("Pedido gerado! Conclua o pagamento.", "info")
    return redirect(url_for('pagamento', compra_id=compra_id))

from flask import jsonify

@app.route('/webhook/asaas', methods=['POST'])
def asaas_webhook():
    """
    URL Oficial para você colar lá no painel do Asaas.
    O Asaas vai bater aqui quando o Pix/Cartão do cliente for aprovado.
    """
    dados = request.json
    
    # Exemplo de lógica de recebimento do Asaas
    if dados and dados.get('event') == 'PAYMENT_RECEIVED':
        payment_id = dados.get('payment', {}).get('id')
        
        # Buscar no banco quem foi que gerou esse pagamento
        compra_res = supabase.table("compras").select("*").eq("asaas_payment_id", payment_id).execute()
        
        if compra_res.data:
            compra = compra_res.data[0]
            if compra['status'] == 'aguardando_pagamento':
                # Atualiza a compra e bloqueia saldo pro vendedor
                supabase.table("compras").update({"status": "pago"}).eq("id", compra['id']).execute()
                supabase.table("artesanatos").update({"disponivel": False}).eq("id", compra['artesanato_id']).execute()
                
                vendedor_res = supabase.table("usuarios").select("carteira_bloqueado").eq("id", compra['vendedor_id']).execute()
                novo_bloqueado = float(vendedor_res.data[0]['carteira_bloqueado'] or 0) + float(compra['valor']) + float(compra['valor_frete'] or 0)
                
                supabase.table("usuarios").update({"carteira_bloqueado": novo_bloqueado}).eq("id", compra['vendedor_id']).execute()
                
    return jsonify({"status": "sucesso"}), 200

@app.route('/pagamento/<compra_id>')
@login_required
def pagamento(compra_id):
    compra = supabase.table("compras").select("*, artesanatos(titulo)").eq("id", compra_id).execute().data[0]
    
    qr_code_image = None
    pix_payload = None
    
    if ASAAS_API_KEY and compra.get('asaas_payment_id'):
        headers = {
            "accept": "application/json",
            "access_token": ASAAS_API_KEY
        }
        req = requests.get(f"{ASAAS_API_URL}/payments/{compra['asaas_payment_id']}/pixQrCode", headers=headers)
        if req.status_code == 200:
            pix_data = req.json()
            qr_code_image = pix_data.get('encodedImage')
            pix_payload = pix_data.get('payload')
            
    return render_template('pagamento.html', compra=compra, qr_code=qr_code_image, payload=pix_payload, key_ativa=bool(ASAAS_API_KEY))

@app.route('/pagamento/mock_sucesso/<compra_id>', methods=['POST'])
@login_required
def mock_pagamento_sucesso(compra_id):
    # Simula o webhook do Asaas confirmando o pagamento
    compra_res = supabase.table("compras").select("*").eq("id", compra_id).execute()
    compra = compra_res.data[0]
    
    if compra['status'] == 'aguardando_pagamento':
        # Atualiza status da compra
        supabase.table("compras").update({"status": "pago"}).eq("id", compra_id).execute()
        
        # Bloqueia o produto
        supabase.table("artesanatos").update({"disponivel": False}).eq("id", compra['artesanato_id']).execute()
        
        # Adiciona o valor como SALDO BLOQUEADO para o vendedor (Produto + Frete)
        vendedor_res = supabase.table("usuarios").select("carteira_bloqueado").eq("id", compra['vendedor_id']).execute()
        saldo_bloqueado_atual = float(vendedor_res.data[0]['carteira_bloqueado'] or 0)
        
        valor_total = float(compra['valor']) + float(compra['valor_frete'] or 0)
        novo_bloqueado = saldo_bloqueado_atual + valor_total
        
        supabase.table("usuarios").update({"carteira_bloqueado": novo_bloqueado}).eq("id", compra['vendedor_id']).execute()
        
        flash("Pagamento confirmado! O dinheiro está retido de forma segura na plataforma. O vendedor já pode despachar.", "success")
        
    return redirect(url_for('perfil'))

@app.route('/compras/despachar/<compra_id>', methods=['POST'])
@login_required
def despachar_compra(compra_id):
    supabase.table("compras").update({"status": "despachado"}).eq("id", compra_id).execute()
    flash("Produto marcado como despachado!", "success")
    return redirect(url_for('perfil'))

@app.route('/compras/receber/<compra_id>', methods=['POST'])
@login_required
def receber_compra(compra_id):
    compra_res = supabase.table("compras").select("*").eq("id", compra_id).execute()
    compra = compra_res.data[0]
    
    if compra['comprador_id'] != session['user_id']:
        return "Acesso negado", 403
        
    if compra['status'] == 'despachado' or compra['status'] == 'pago':
        # Libera o dinheiro
        supabase.table("compras").update({"status": "entregue"}).eq("id", compra_id).execute()
        
        vendedor_res = supabase.table("usuarios").select("carteira_saldo, carteira_bloqueado").eq("id", compra['vendedor_id']).execute()
        v = vendedor_res.data[0]
        
        valor_total = float(compra['valor']) + float(compra['valor_frete'] or 0)
        novo_saldo = float(v['carteira_saldo'] or 0) + valor_total
        novo_bloqueado = float(v['carteira_bloqueado'] or 0) - valor_total
        
        # Corrige bloqueado se ficar negativo por segurança
        if novo_bloqueado < 0: novo_bloqueado = 0
        
        supabase.table("usuarios").update({
            "carteira_saldo": novo_saldo,
            "carteira_bloqueado": novo_bloqueado
        }).eq("id", compra['vendedor_id']).execute()
        
        flash("Recebimento confirmado! O dinheiro foi liberado para a carteira do vendedor.", "success")
        
    return redirect(url_for('perfil'))

# --- ROTAS DE ARTESANATO ---

@app.route('/artesanatos')
def listar_artesanatos():
    res = supabase.table("artesanatos").select("*, categorias(nome)").execute()
    return render_template('artesanatos/lista.html', artesanatos=res.data)

@app.route('/artesanatos/novo', methods=['GET', 'POST'])
@login_required
def novo_artesanato():
    if session.get('tipo') != 'vendedor' and not session.get('is_admin'):
        flash("Apenas Vendedores podem anunciar produtos.", "warning")
        return redirect(url_for('index'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        preco = request.form.get('preco')
        categoria_id = request.form.get('categoria_id')
        aldeia = request.form.get('aldeia')
        
        imagem = request.files.get('imagem')
        imagem_url = None
        if imagem and imagem.filename:
            ext = imagem.filename.rsplit('.', 1)[-1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            file_bytes = imagem.read()
            try:
                supabase.storage.from_("artesanato_fotos").upload(file=file_bytes, path=filename, file_options={"content-type": imagem.content_type})
                imagem_url = supabase.storage.from_("artesanato_fotos").get_public_url(filename)
            except Exception as e:
                print(f"Erro no upload: {e}")
        
        supabase.table("artesanatos").insert({
            "titulo": titulo, "descricao": descricao, "preco": float(preco),
            "categoria_id": int(categoria_id), "usuario_id": session['user_id'],
            "aldeia": aldeia, "imagem_url": imagem_url
        }).execute()
        flash("Artesanato postado com sucesso!", "success")
        return redirect(url_for('listar_artesanatos'))
    
    categorias = supabase.table("categorias").select("*").execute()
    return render_template('artesanatos/novo.html', categorias=categorias.data)

@app.route('/artesanatos/<id>')
def detalhe_artesanato(id):
    art_res = supabase.table("artesanatos").select("*, categorias(nome), usuarios(nome, email)").eq("id", id).execute()
    comentarios = supabase.table("comentarios").select("*, usuarios(nome)").eq("artesanato_id", id).order("criado_em").execute()
    interesses = supabase.table("interesses").select("*").eq("artesanato_id", id).execute()
    
    if not art_res.data:
        return redirect(url_for('listar_artesanatos'))
        
    return render_template('artesanatos/detalhe.html', artesanato=art_res.data[0], comentarios=comentarios.data, total_interesses=len(interesses.data))

@app.route('/artesanatos/<id>/editar', methods=['GET', 'POST'])
@login_required
def editar_artesanato(id):
    art_res = supabase.table("artesanatos").select("*").eq("id", id).execute()
    if not art_res.data:
        flash("Artesanato não encontrado.", "danger")
        return redirect(url_for('listar_artesanatos'))
    
    art = art_res.data[0]
    if art['usuario_id'] != session['user_id'] and not session.get('is_admin'):
        flash("Acesso negado.", "danger")
        return redirect(url_for('listar_artesanatos'))

    if request.method == 'POST':
        update_data = {
            "titulo": request.form.get('titulo'),
            "descricao": request.form.get('descricao'),
            "preco": float(request.form.get('preco')),
            "categoria_id": int(request.form.get('categoria_id')),
            "aldeia": request.form.get('aldeia'),
            "disponivel": request.form.get('disponivel') == 'True'
        }

        imagem = request.files.get('imagem')
        if imagem and imagem.filename:
            ext = imagem.filename.rsplit('.', 1)[-1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            file_bytes = imagem.read()
            try:
                supabase.storage.from_("artesanato_fotos").upload(file=file_bytes, path=filename, file_options={"content-type": imagem.content_type})
                update_data["imagem_url"] = supabase.storage.from_("artesanato_fotos").get_public_url(filename)
            except Exception as e:
                print(f"Erro no upload da imagem: {e}")

        supabase.table("artesanatos").update(update_data).eq("id", id).execute()
        flash("Artesanato atualizado!", "success")
        return redirect(url_for('detalhe_artesanato', id=id))

    categorias = supabase.table("categorias").select("*").execute()
    return render_template('artesanatos/editar.html', artesanato=art, categorias=categorias.data)

@app.route('/artesanatos/<id>/deletar', methods=['POST'])
@login_required
def deletar_artesanato(id):
    art_res = supabase.table("artesanatos").select("usuario_id").eq("id", id).execute()
    if art_res.data and (art_res.data[0]['usuario_id'] == session['user_id'] or session.get('is_admin')):
        supabase.table("artesanatos").delete().eq("id", id).execute()
        flash("Removido com sucesso.", "success")
    else:
        flash("Permissão negada.", "danger")
    return redirect(url_for('listar_artesanatos'))

@app.route('/artesanatos/<id>/interesse', methods=['POST'])
@login_required
def registrar_interesse(id):
    supabase.table("interesses").insert({"usuario_id": session['user_id'], "artesanato_id": id}).execute()
    flash("Interesse registrado!", "success")
    return redirect(url_for('detalhe_artesanato', id=id))

@app.route('/artesanatos/<id>/comentario', methods=['POST'])
@login_required
def adicionar_comentario(id):
    conteudo = request.form.get('conteudo')
    if conteudo:
        supabase.table("comentarios").insert({"conteudo": conteudo, "usuario_id": session['user_id'], "artesanato_id": id}).execute()
        flash("Comentário adicionado!", "success")
    return redirect(url_for('detalhe_artesanato', id=id))

@app.route('/busca')
def busca():
    query_text = request.args.get('q', '')
    cat_id = request.args.get('categoria', '')
    aldeia = request.args.get('aldeia', '')
    
    query = supabase.table("artesanatos").select("*, categorias(nome)")
    
    if query_text:
        query = query.ilike("titulo", f"%{query_text}%")
    if cat_id:
        query = query.eq("categoria_id", cat_id)
    if aldeia:
        query = query.ilike("aldeia", f"%{aldeia}%")
        
    res = query.execute()
    categorias = supabase.table("categorias").select("*").execute()
    return render_template('busca.html', artesanatos=res.data, categorias=categorias.data)

@app.route('/eventos')
def listar_eventos():
    res = supabase.table("eventos").select("*, usuarios(nome)").order("data_evento").execute()
    return render_template('eventos/lista.html', eventos=res.data)

@app.route('/eventos/novo', methods=['GET', 'POST'])
@login_required
def novo_evento():
    if request.method == 'POST':
        supabase.table("eventos").insert({
            "titulo": request.form.get('titulo'),
            "descricao": request.form.get('descricao'),
            "data_evento": request.form.get('data_evento'),
            "local": request.form.get('local'),
            "usuario_id": session['user_id']
        }).execute()
        flash("Evento criado!", "success")
        return redirect(url_for('listar_eventos'))
    return render_template('eventos/novo.html')

@app.route('/eventos/<id>')
def detalhe_evento(id):
    res = supabase.table("eventos").select("*, usuarios(nome)").eq("id", id).execute()
    if not res.data:
        flash("Evento não encontrado.", "danger")
        return redirect(url_for('listar_eventos'))
    return render_template('eventos/detalhe.html', evento=res.data[0])

if __name__ == '__main__':
    with app.app_context():
        create_admin()
        seed_categories()
    app.run(debug=True)
