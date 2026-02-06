import cv2
from ultralytics import YOLO
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
import csv
from PIL import ImageTk, Image
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Bibliotecas para Hardware
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import serial 

# --- 1. GESTÃO DE CONFIGURAÇÃO ---
def guia_telegram():
    janela = tk.Toplevel()
    janela.title("Ajuda - Configurar Telegram")
    janela.geometry("500x400")
    texto = (
        "🤖 PASSO A PASSO TELEGRAM:\n\n"
        "1. Abra o Telegram e procure por @BotFather.\n"
        "2. Envie o comando /newbot e siga as instruções.\n"
        "3. Copie o 'API Token' gerado e cole no campo ao lado.\n"
        "4. Inicie uma conversa com seu novo bot.\n"
        "5. No Setup, clique em 'Vincular ID' e escaneie o QR Code."
    )
    tk.Label(janela, text=texto, justify="left", padx=20, pady=20, font=("Arial", 10)).pack()
    tk.Button(janela, text="Abrir @BotFather no Navegador", command=lambda: webbrowser.open("https://t.me/botfather"), bg="#0088cc", fg="white").pack(pady=5)
    tk.Button(janela, text="Fechar", command=janela.destroy).pack(pady=10)

def guia_email():
    janela = tk.Toplevel()
    janela.title("Ajuda - Senha de App Google")
    janela.geometry("500x450")
    texto = (
        "📧 PASSO A PASSO E-MAIL (GMAIL):\n\n"
        "1. Ative a 'Verificação em Duas Etapas' na sua conta Google.\n"
        "2. Vá em 'Segurança' > 'Senhas de App'.\n"
        "3. Em 'App', selecione 'Outro' e dê o nome 'LabInd'.\n"
        "4. O Google gerará uma senha de 16 caracteres.\n"
        "5. COPIE ESSA SENHA e cole no campo 'Senha de App' do Monitor.\n\n"
        "⚠️ Importante: Não use sua senha normal do e-mail!"
    )
    tk.Label(janela, text=texto, justify="left", padx=20, pady=20, font=("Arial", 10)).pack()
    tk.Button(janela, text="Ir para Senhas de App (Google)", command=lambda: webbrowser.open("https://myaccount.google.com/apppasswords"), bg="#4285F4", fg="white").pack(pady=5)
    tk.Button(janela, text="Fechar", command=janela.destroy).pack(pady=10)

def carregar_configuracoes():
    # 1. Definimos TODAS as chaves que o programa precisa para rodar
    defaults = {
        "preferencia_notificacao": "Ambos",
        "telegram_token": "", "telegram_chat_id": "", "limite_persistencia": 30,
        "nome_laboratorio": "LabInd - Impressora 01",
        "email_remetente": "", "email_senha": "", "email_destino": "",
        "smtp_server": "smtp.gmail.com", "smtp_port": 587,
        "parar_automatica": False,
        "tipo_conexao": "BambuMQTT",
        "bambu_ip": "192.168.100.81",
        "bambu_access_code": "",
        "bambu_serial": "",
        "serial_port": "COM3",
        "serial_gcode": "M112"
    }
    
    caminho_config = 'config.json'
    if os.path.exists(caminho_config):
        with open(caminho_config, 'r') as f:
            try:
                config_salva = json.load(f)
                # 2. Mescla o que está salvo com os defaults
                # Isso garante que campos novos apareçam mesmo em arquivos velhos
                defaults.update(config_salva)
            except:
                pass
    return defaults

def registrar_log_csv(tipo, impressora):
    caminho_log = 'historico_falhas.csv'
    existe = os.path.exists(caminho_log)
    with open(caminho_log, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(['Data', 'Hora', 'Impressora', 'Falha'])
        writer.writerow([datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%H:%M:%S'), impressora, tipo])

def abrir_janela_setup(config_atual):
    root = tk.Tk()
    root.title("Configuração Industrial - LabInd")
    root.geometry("550x680")

    container = tk.Frame(root); container.pack(fill="both", expand=True)
    canvas = tk.Canvas(container); scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
    
    # --- VARIÁVEIS DE CONTROLE ---
    var_escolha = tk.StringVar(value=config_atual.get("preferencia_notificacao", "Ambos"))
    var_parar = tk.BooleanVar(value=config_atual.get("parar_automatica", False))
    var_tipo_hw = tk.StringVar(value=config_atual.get("tipo_conexao", "BambuMQTT"))

    # --- LÓGICA DE BOTÕES ---
    def vincular_telegram():
        token = entry_token.get()
        if not token: 
            messagebox.showwarning("Aviso", "Insira o Token primeiro!"); return
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
            if r["ok"]:
                img_qr = ImageTk.PhotoImage(qrcode.make(f"https://t.me/{r['result']['username']}").resize((130, 130)))
                label_qr.config(image=img_qr); label_qr.image = img_qr
                label_status_qr.config(text="✅ Envie uma mensagem ao Bot!", fg="green")
                
                def escutar():
                    requests.get(f"https://api.telegram.org/bot{token}/getUpdates?offset=-1")
                    for _ in range(30):
                        time.sleep(2)
                        resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates").json()
                        if resp["ok"] and len(resp["result"]) > 0:
                            novo_id = resp["result"][-1]["message"]["chat"]["id"]
                            entry_id.delete(0, tk.END); entry_id.insert(0, str(novo_id))
                            label_status_qr.config(text="✅ Vinculado com sucesso!", fg="green"); return
                threading.Thread(target=escutar, daemon=True).start()
        except: label_status_qr.config(text="❌ Erro de Token/Rede", fg="red")

    def teste_rapido_bambu():
        # Função de diagnóstico para o TCC
        try:
            client = mqtt.Client(CallbackAPIVersion.VERSION2)
            client.tls_set(cert_reqs=mqtt.ssl.CERT_NONE)
            client.username_pw_set("bblp", ent_b_code.get()) # Usa ent_b_code
            client.connect(ent_b_ip.get(), 8883, 5)          # Usa ent_b_ip
            messagebox.showinfo("Sucesso", "✅ Conexão MQTT estabelecida!\nA impressora respondeu.")
            client.disconnect()
        except Exception as e:
            messagebox.showerror("Falha", f"❌ Sem conexão:\n{e}")

    def atualizar_interface():
        # 1. Notificações
        esc = var_escolha.get()
        st_tg = "normal" if esc in ["Telegram", "Ambos"] else "disabled"
        st_em = "normal" if esc in ["Email", "Ambos"] else "disabled"
        
        entry_token.config(state=st_tg); entry_id.config(state=st_tg); btn_vincular.config(state=st_tg)
        entry_rem.config(state=st_em); entry_sen.config(state=st_em); entry_des.config(state=st_em)
        
        # 2. Hardware (Aqui estava o erro: nomes padronizados)
        ativo = var_parar.get()
        tipo = var_tipo_hw.get()
        st_b = "normal" if ativo and tipo == "BambuMQTT" else "disabled"
        st_s = "normal" if ativo and tipo == "Serial" else "disabled"
        
        ent_b_ip.config(state=st_b); ent_b_code.config(state=st_b); ent_b_ser.config(state=st_b)
        ent_s_port.config(state=st_s); ent_s_gcode.config(state=st_s)

    def salvar():
        config_atual.update({
            "preferencia_notificacao": var_escolha.get(), "telegram_token": entry_token.get(), "telegram_chat_id": entry_id.get(),
            "email_remetente": entry_rem.get(), "email_senha": entry_sen.get(), "email_destino": entry_des.get(),
            "nome_laboratorio": entry_lab.get(), "parar_automatica": var_parar.get(), "tipo_conexao": var_tipo_hw.get(),
            # Nomes corrigidos para salvar corretamente
            "bambu_ip": ent_b_ip.get(), "bambu_access_code": ent_b_code.get(), "bambu_serial": ent_b_ser.get(),
            "serial_port": ent_s_port.get(), "serial_gcode": ent_s_gcode.get()
        })
        with open('config.json', 'w') as f: json.dump(config_atual, f, indent=4)
        root.destroy()

    # --- UI LAYOUT ---
    tk.Label(scrollable_frame, text="Configuração LabInd", font=("Arial", 12, "bold")).pack(pady=10)

    # SEÇÃO 1: ALERTAS
    f1 = tk.LabelFrame(scrollable_frame, text=" 1. Notificações e Alertas ", padx=10, pady=10)
    f1.pack(fill="x", padx=20, pady=5)

    # Botões de Rádio (Alinhados à Esquerda)
    f_rad = tk.Frame(f1); f_rad.pack(fill="x", pady=(0, 10))
    for t, v in [("Telegram", "Telegram"), ("E-mail", "Email"), ("Ambos", "Ambos")]:
        tk.Radiobutton(f_rad, text=t, variable=var_escolha, value=v, command=atualizar_interface).pack(side="left", padx=(0, 10))
    
    # --- SUB-SEÇÃO TELEGRAM ---
    # Linha de Título + Ajuda (Na mesma linha)
    f_tg_head = tk.Frame(f1); f_tg_head.pack(fill="x")
    tk.Label(f_tg_head, text="Token do Bot:", font=("Arial", 9, "bold")).pack(side="left")
    tk.Button(f_tg_head, text="❓ Obter Token", command=guia_telegram, fg="#0088cc", bd=0, cursor="hand2", font=("Arial", 8)).pack(side="right")
    
    entry_token = tk.Entry(f1, width=50); entry_token.insert(0, config_atual.get("telegram_token", ""))
    entry_token.pack(fill="x", pady=(0, 5)) # fill="x" estica o campo
    
    tk.Label(f1, text="Chat ID:", font=("Arial", 9)).pack(anchor="w")
    f_id_row = tk.Frame(f1); f_id_row.pack(fill="x", pady=(0, 10))
    entry_id = tk.Entry(f_id_row, width=20); entry_id.insert(0, config_atual.get("telegram_chat_id", ""))
    entry_id.pack(side="left")
    
    # Botão de QR Code menor e ao lado do ID ou abaixo
    btn_vincular = tk.Button(f_id_row, text="📷 Vincular via QR Code", command=vincular_telegram, bg="#0088cc", fg="white", font=("Arial", 8))
    btn_vincular.pack(side="left", padx=10)
    
    # Área para mostrar o QR Code e status (centralizado para destaque)
    label_qr = tk.Label(f1); label_qr.pack()
    label_status_qr = tk.Label(f1, text="", font=("Arial", 8)); label_status_qr.pack()

    # Separador Visual
    tk.Frame(f1, height=1, bg="#dddddd").pack(fill="x", pady=10)

    # --- SUB-SEÇÃO EMAIL ---
    # Linha de Título + Ajuda
    f_em_head = tk.Frame(f1); f_em_head.pack(fill="x")
    tk.Label(f_em_head, text="E-mail Remetente (Gmail):", font=("Arial", 9, "bold")).pack(side="left")
    tk.Button(f_em_head, text="🔑 Gerar Senha de App", command=guia_email, fg="#0088cc", bd=0, cursor="hand2", font=("Arial", 8)).pack(side="right")
    
    entry_rem = tk.Entry(f1, width=50); entry_rem.insert(0, config_atual.get("email_remetente", ""))
    entry_rem.pack(fill="x", pady=(0, 5))
    
    tk.Label(f1, text="Senha de App (16 dígitos):", font=("Arial", 9)).pack(anchor="w")
    entry_sen = tk.Entry(f1, width=30, show="*"); entry_sen.insert(0, config_atual.get("email_senha", ""))
    entry_sen.pack(anchor="w", pady=(0, 5))
    
    tk.Label(f1, text="E-mail de Destino:", font=("Arial", 9)).pack(anchor="w")
    entry_des = tk.Entry(f1, width=50); entry_des.insert(0, config_atual.get("email_destino", ""))
    entry_des.pack(fill="x")

    # SEÇÃO 2: HARDWARE
    f2 = tk.LabelFrame(scrollable_frame, text=" 2. Controle de Hardware (Kill Switch) ", padx=10, pady=10)
    f2.pack(fill="x", padx=20, pady=10)
    
    tk.Checkbutton(f2, text="Ativar Parada Automática", variable=var_parar, command=atualizar_interface, font=("bold")).pack(anchor="w")
    
    # --- Interface Bambu Lab (Corrigida: Nomes ent_b_... e Botão Testar) ---
    tk.Radiobutton(f2, text="Bambu Lab (MQTT)", variable=var_tipo_hw, value="BambuMQTT", command=atualizar_interface).pack(anchor="w", pady=(5,0))
    f_b = tk.Frame(f2)
    f_b.pack(fill="x", padx=10)
    
    # Linha 1: IP + Botão Testar + Code
    tk.Label(f_b, text="IP:").grid(row=0, column=0)
    ent_b_ip = tk.Entry(f_b, width=15) # Nome corrigido de ent_ip para ent_b_ip
    ent_b_ip.insert(0, config_atual.get("bambu_ip", ""))
    ent_b_ip.grid(row=0, column=1)
    
    # Botão Testar Integrado
    tk.Button(f_b, text="⚡ Testar", command=teste_rapido_bambu, bg="#f39c12", fg="white", font=("Arial", 7, "bold")).grid(row=0, column=2, padx=5)
    
    tk.Label(f_b, text="Code:").grid(row=0, column=3)
    ent_b_code = tk.Entry(f_b, width=10, show="*") # Nome corrigido de ent_code para ent_b_code
    ent_b_code.insert(0, config_atual.get("bambu_access_code", ""))
    ent_b_code.grid(row=0, column=4)
    
    # Linha 2: Serial da Máquina
    tk.Label(f_b, text="Serial:").grid(row=1, column=0, pady=5)
    ent_b_ser = tk.Entry(f_b, width=25) # Nome corrigido de ent_ser para ent_b_ser
    ent_b_ser.insert(0, config_atual.get("bambu_serial", ""))
    ent_b_ser.grid(row=1, column=1, columnspan=4, sticky="w")

    # --- Interface Serial Universal (Corrigida: Nomes ent_s_...) ---
    tk.Radiobutton(f2, text="Serial (USB/Marlin)", variable=var_tipo_hw, value="Serial", command=atualizar_interface).pack(anchor="w", pady=(10,0))
    f_s = tk.Frame(f2)
    f_s.pack(fill="x", padx=10)
    
    tk.Label(f_s, text="Porta:").grid(row=0, column=0)
    ent_s_port = tk.Entry(f_s, width=10) # Nome corrigido de ent_port para ent_s_port
    ent_s_port.insert(0, config_atual.get("serial_port", ""))
    ent_s_port.grid(row=0, column=1, padx=5)
    
    tk.Label(f_s, text="G-Code:").grid(row=0, column=2)
    ent_s_gcode = tk.Entry(f_s, width=8) # Nome corrigido de ent_gc para ent_s_gcode
    ent_s_gcode.insert(0, config_atual.get("serial_gcode", "M112"))
    ent_s_gcode.grid(row=0, column=3)

    # FINALIZAÇÃO
    tk.Label(scrollable_frame, text="\nNome do Equipamento:").pack()
    entry_lab = tk.Entry(scrollable_frame, width=40); entry_lab.insert(0, config_atual.get("nome_laboratorio", "")); entry_lab.pack()
    tk.Button(scrollable_frame, text="SALVAR E INICIAR", command=salvar, bg="green", fg="white", font=("Arial", 11, "bold"), pady=10).pack(pady=20)
    
    atualizar_interface()
    root.mainloop()

# --- 2. LÓGICA DE ALERTA E PARADA (THREADED) ---
def executar_kill_switch(config):
    # Novo: Lógica de hardware integrada
    if not config.get("parar_automatica"): return
    
    if config["tipo_conexao"] == "BambuMQTT":
        try:
            client = mqtt.Client(CallbackAPIVersion.VERSION2)
            client.tls_set(cert_reqs=mqtt.ssl.CERT_NONE)
            client.username_pw_set("bblp", config["bambu_access_code"])
            client.connect(config["bambu_ip"], 8883, 60)
            payload = {"print": {"sequence_id": "1", "command": "pause", "param": ""}}
            client.publish(f"device/{config['bambu_serial']}/request", json.dumps(payload), qos=1)
            print("🛑 Comando MQTT de Pausa enviado!")
            client.disconnect()
        except Exception as e: print(f"Erro MQTT: {e}")
        
    elif config["tipo_conexao"] == "Serial":
        try:
            with serial.Serial(config["serial_port"], 115200, timeout=1) as ser:
                ser.write(str.encode(f"{config['serial_gcode']}\r\n"))
                print(f"🛑 G-Code {config['serial_gcode']} enviado!")
        except Exception as e: print(f"Erro Serial: {e}")

def disparar_alertas_background(tipo, frame, config):
    if not os.path.exists('capturas'): os.makedirs('capturas')
    horario = datetime.now().strftime('%H:%M:%S')
    caminho = os.path.join('capturas', f"alerta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
    cv2.imwrite(caminho, frame)
    texto = f"⚠️ FALHA: {tipo} no {config['nome_laboratorio']} às {horario}"
    registrar_log_csv(tipo, config['nome_laboratorio'])
    
    # 1. Hardware Stop (Ação Imediata)
    executar_kill_switch(config)
    
    # 2. Notificações
    pref = config.get("preferencia_notificacao", "Ambos")
    if pref in ["Telegram", "Ambos"]:
        try:
            url = f"https://api.telegram.org/bot{config['telegram_token']}"
            requests.post(f"{url}/sendMessage", data={'chat_id': config['telegram_chat_id'], 'text': texto}, timeout=10)
            with open(caminho, 'rb') as f: requests.post(f"{url}/sendPhoto", data={'chat_id': config['telegram_chat_id']}, files={'photo': f}, timeout=10)
        except: pass
    if pref in ["Email", "Ambos"]:
        try:
            msg = MIMEMultipart(); msg['From'] = config["email_remetente"]; msg['To'] = config["email_destino"]; msg['Subject'] = texto
            with open(caminho, 'rb') as f: msg.attach(MIMEImage(f.read(), name="falha.jpg"))
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as s:
                s.starttls(); s.login(config["email_remetente"], config["email_senha"]); s.send_message(msg)
        except: pass

# --- 3. LOOP PRINCIPAL ---

config = carregar_configuracoes()
if not config.get("telegram_token") and not config.get("email_remetente"):
    abrir_janela_setup(config); config = carregar_configuracoes()

model = YOLO("models/best.pt")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
classNames = ['spaghetti', 'stringing', 'zits']
contador, confirmado = 0, False

while True:
    ret, img = cap.read()
    if not ret: break
    altura, largura, _ = img.shape

    results = model(img, stream=True, conf=0.5)
    detectou, classe = False, ""
    for r in results:
        for box in r.boxes:
            detectou = True; x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
            classe = classNames[int(box.cls[0])]
            cv2.putText(img, f'{classe}', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

    # Lógica de Buffer
    limite = config.get("limite_persistencia", 30)
    if detectou: contador = min(limite, contador + 1)
    else: contador = max(0, contador - 1)

    if contador >= limite and not confirmado:
        threading.Thread(target=disparar_alertas_background, args=(classe, img.copy(), config)).start()
        confirmado = True
    elif contador == 0: confirmado = False

    # --- DASHBOARD VISUAL (DINÂMICO) ---
    # Cria a barra preta no topo baseada na largura da imagem
    cv2.rectangle(img, (0, 0), (largura, 45), (0, 0, 0), -1)
    
    status_cor = (0, 0, 255) if detectou else (0, 255, 0)
    # Texto à Esquerda: Status da Máquina
    cv2.putText(img, f"{config.get('nome_laboratorio')} | Falha: {contador}/{limite}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_cor, 2)
    
    # Texto à Direita: Comandos (Posição calculada dinamicamente)
    cv2.putText(img, "[S] Setup | [Q] Sair", (largura - 190, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow('Monitor Industrial LabInd', img)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'): 
        cap.release(); cv2.destroyAllWindows()
        abrir_janela_setup(config)
        config = carregar_configuracoes() # Recarrega para evitar KeyError
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if key == ord('q'): break

cap.release(); cv2.destroyAllWindows()