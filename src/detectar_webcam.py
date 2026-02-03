import cv2
from ultralytics import YOLO
import math
import requests
from datetime import datetime
import json
import os
import tkinter as tk
from tkinter import messagebox
import threading
import time
import webbrowser
import qrcode
from PIL import ImageTk, Image

# --- 1. GESTÃO DE CONFIGURAÇÃO ---
def carregar_configuracoes():
    caminho_config = 'config.json'
    if os.path.exists(caminho_config):
        with open(caminho_config, 'r') as f:
            return json.load(f)
    return {
        "telegram_token": "",
        "telegram_chat_id": "",
        "limite_persistencia": 30,
        "nome_laboratorio": "LabInd - Impressora 01"
    }

def abrir_ajuda():
    janela_ajuda = tk.Toplevel()
    janela_ajuda.title("Guia de Configuração - LabInd")
    janela_ajuda.geometry("500x500")
    janela_ajuda.configure(bg="#f9f9f9")

    conteudo = (
        "🔍 PASSO A PASSO PARA CONFIGURAÇÃO\n\n"
        "1. CRIAR SEU BOT (TOKEN):\n"
        "   • Clique no botão azul 'Abrir @BotFather'.\n"
        "   • Mande /newbot e siga as instruções.\n"
        "   • Copie o 'API Token' e cole na tela de configuração.\n\n"
        "2. VINCULAR SEU CELULAR (ID):\n"
        "   • Com o Token colado, clique em 'Ativar Vínculo'.\n"
        "   • Um QR Code aparecerá. Escaneie-o com seu celular.\n"
        "   • No Telegram, clique em 'COMEÇAR' e mande um 'Oi'.\n"
        "   • O sistema detectará seu ID automaticamente!\n\n"
        "3. MONITORAMENTO:\n"
        "   • Salve as configurações e a câmera abrirá.\n"
        "   • A IA monitora falhas de spaghetti, stringing e zits."
    )

    tk.Label(janela_ajuda, text=conteudo, justify="left", padx=25, pady=25, 
             font=("Arial", 10), bg="#f9f9f9").pack()
    tk.Button(janela_ajuda, text="Entendi!", command=janela_ajuda.destroy, bg="#007bff", fg="white").pack(pady=10)

def abrir_janela_setup(config_atual):
    def abrir_link(url):
        webbrowser.open_new(url)

    def gerar_qr_code(token):
        try:
            url_get_me = f"https://api.telegram.org/bot{token}/getMe"
            resp = requests.get(url_get_me).json()
            if resp["ok"]:
                bot_username = resp["result"]["username"]
                link_bot = f"https://t.me/{bot_username}"
                qr = qrcode.make(link_bot).resize((140, 140))
                img_qr = ImageTk.PhotoImage(qr)
                label_qr.config(image=img_qr)
                label_qr.image = img_qr
                label_status_qr.config(text="✅ Escaneie para abrir seu Bot!", fg="green")
        except:
            label_status_qr.config(text="❌ Token inválido para QR Code", fg="red")

    def vincular_automatico():
        token = entry_token.get()
        if not token:
            messagebox.showwarning("Aviso", "Insira o Token primeiro!")
            return
        
        gerar_qr_code(token)
        btn_vincular.config(text="⌛ Aguardando sinal...", bg="yellow", fg="black")
        
        def escutar_telegram():
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            try:
                requests.get(url + "?offset=-1")
                for _ in range(30):
                    response = requests.get(url).json()
                    if response["ok"] and len(response["result"]) > 0:
                        novo_id = response["result"][-1]["message"]["chat"]["id"]
                        entry_id.delete(0, tk.END); entry_id.insert(0, str(novo_id))
                        btn_vincular.config(text="✅ ID Vinculado!", bg="lightgreen")
                        return
                    time.sleep(2)
                btn_vincular.config(text="❌ Tempo esgotado", bg="red", fg="white")
            except:
                messagebox.showerror("Erro", "Falha de conexão.")

        threading.Thread(target=escutar_telegram, daemon=True).start()

    def salvar():
        config_atual.update({
            "telegram_token": entry_token.get(),
            "telegram_chat_id": entry_id.get(),
            "nome_laboratorio": entry_lab.get()
        })
        with open('config.json', 'w') as f:
            json.dump(config_atual, f, indent=4)
        root.destroy()

    root = tk.Tk()
    root.title("Setup Visual LabInd")
    root.geometry("480x650")

    tk.Label(root, text="Ativação do Monitor Modular", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Button(root, text="❓ Precisa de ajuda? Clique aqui", command=abrir_ajuda, fg="blue", bd=0, cursor="hand2").pack()

    # PASSO 1
    tk.Label(root, text="\n1. Crie seu Bot no Telegram:", font=("Arial", 10, "bold")).pack()
    tk.Button(root, text="Abrir @BotFather", command=lambda: abrir_link("https://t.me/botfather"), bg="#0088cc", fg="white").pack(pady=5)
    entry_token = tk.Entry(root, width=50); entry_token.insert(0, config_atual["telegram_token"])
    entry_token.pack(pady=2)

    # PASSO 2
    tk.Label(root, text="\n2. Vincule seu Celular:", font=("Arial", 10, "bold")).pack()
    btn_vincular = tk.Button(root, text="Ativar Vínculo e Gerar QR Code", command=vincular_automatico, bg="blue", fg="white")
    btn_vincular.pack(pady=5)
    
    label_status_qr = tk.Label(root, text="O QR Code aparecerá aqui", font=("Arial", 8, "italic"))
    label_status_qr.pack()
    label_qr = tk.Label(root); label_qr.pack(pady=5)

    # DADOS FINAIS
    tk.Label(root, text="Chat ID detectado:").pack()
    entry_id = tk.Entry(root, width=30); entry_id.insert(0, config_atual["telegram_chat_id"])
    entry_id.pack()

    tk.Label(root, text="Nome da Impressora:").pack()
    entry_lab = tk.Entry(root, width=30); entry_lab.insert(0, config_atual["nome_laboratorio"])
    entry_lab.pack()

    tk.Button(root, text="SALVAR E INICIAR", command=salvar, bg="green", fg="white", font=("Arial", 11, "bold")).pack(pady=20)
    root.mainloop()

# --- 2. INICIALIZAÇÃO ---
config = carregar_configuracoes()
if not config["telegram_token"] or not config["telegram_chat_id"]:
    abrir_janela_setup(config)
    config = carregar_configuracoes()

TOKEN, CHAT_ID = config["telegram_token"], config["telegram_chat_id"]
LIMITE_ALERTA, NOME_LAB = config["limite_persistencia"], config["nome_laboratorio"]

model = YOLO("models/best.pt") #
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) #
classNames = ['spaghetti', 'stringing', 'zits'] #

contador_falhas = 0
falha_confirmada = False

def enviar_alerta(tipo, frame):
    horario_arquivo = datetime.now().strftime("%Y%m%d_%H%M%S")
    horario_msg = datetime.now().strftime("%H:%M:%S")
    
    # Cria a pasta de capturas se ela não existir
    if not os.path.exists('capturas'):
        os.makedirs('capturas')
    
    caminho_foto = os.path.join('capturas', f"alerta_{horario_arquivo}.jpg")
    msg = f"⚠️ *FALHA NO {NOME_LAB}*\n📌 *Erro:* {tipo}\n⏰ *Hora:* {horario_msg}"

    try:
        cv2.imwrite(caminho_foto, frame)
        # Envia a mensagem
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
        # Envia a foto salva na pasta capturas
        with open(caminho_foto, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                          data={'chat_id': CHAT_ID}, files={'photo': f})
        print(f"✅ Alerta enviado e salvo em: {caminho_foto}")
    except: 
        print("❌ Erro no envio do alerta.")

# --- 3. LOOP PRINCIPAL ---
while True:
    success, img = cap.read() #
    if not success: break

    results = model(img, stream=True, conf=0.5) #
    detectou = False
    current_class = ""

    for r in results: #
        for box in r.boxes: #
            detectou = True
            x1, y1, x2, y2 = map(int, box.xyxy[0]) #
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3) #
            current_class = classNames[int(box.cls[0])] #
            cv2.putText(img, f'{current_class}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2) #

    if detectou: contador_falhas += 1
    else: contador_falhas = max(0, contador_falhas - 1)

    if contador_falhas >= LIMITE_ALERTA and not falha_confirmada:
        enviar_alerta(current_class, img)
        falha_confirmada = True
    elif contador_falhas == 0:
        falha_confirmada = False

    cv2.imshow('Monitor LabInd', img) #
    key = cv2.waitKey(1) & 0xFF #
    if key == ord('s'): 
        cap.release(); cv2.destroyAllWindows()
        abrir_janela_setup(config)
        config = carregar_configuracoes()
        TOKEN, CHAT_ID = config["telegram_token"], config["telegram_chat_id"]
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if key == ord('q'): break #

cap.release() #
cv2.destroyAllWindows() #