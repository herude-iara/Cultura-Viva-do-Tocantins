import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"DEBUG: URL do Supabase -> {url}")
supabase: Client = create_client(url, key)

print("Tentando inserir dados diretamente via API (usando as chaves do .env)...")

try:
    # 1. Inserir Categoria
    res_cat = supabase.table("categorias").insert({"nome": "Teste Categoria"}).execute()
    print("Sucesso ao inserir Categoria!")
    
    # 2. Inserir Usuário
    res_user = supabase.table("usuarios").insert({
        "nome": "User API", 
        "email": "api@teste.com", 
        "senha": "123", 
        "is_admin": True
    }).execute()
    print("Sucesso ao inserir Usuário!")
    user_id = res_user.data[0]['id']
    cat_id = res_cat.data[0]['id']
    
    # 3. Inserir Artesanato
    res_art = supabase.table("artesanatos").insert({
        "titulo": "Artesanato da API",
        "descricao": "Teste de inserção direta.",
        "preco": 99.99,
        "categoria_id": cat_id,
        "usuario_id": user_id,
        "aldeia": "Teste",
        "disponivel": True
    }).execute()
    print("Sucesso ao inserir Artesanato!")
    
except Exception as e:
    print(f"\nERRO CRÍTICO NA API: {e}")
    print("Isso significa que o banco DESTE projeto do .env ainda tem bloqueios de segurança (RLS) ativos ou deu outro erro.")

print("\nVerificando o que tem no banco agora...")
print(f"Artesanatos no banco: {len(supabase.table('artesanatos').select('*').execute().data)}")


