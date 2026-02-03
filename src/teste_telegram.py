import requests

# Substitua com seus dados reais
TOKEN = "8209383154:AAFTVenCCcCN-WCtZyVYq1FF02f4kd1Ydhc"
CHAT_ID = "7375435501"

def testar_conexao():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "🚀 *Teste de Sistema - LabInd*\n\nConexão estabelecida com sucesso! O seu Bot está pronto para monitorar as falhas de impressão.",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Sucesso! Verifique seu Telegram.")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Falha na rede: {e}")

if __name__ == "__main__":
    testar_conexao()