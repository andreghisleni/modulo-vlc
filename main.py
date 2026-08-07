import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time

# ==========================================
# CONFIGURAÇÕES
# ==========================================
API_BASE_URL = "http://localhost:3004" # Não coloque a barra no final
API_KEY = "sua_chave_aqui" # Substitua pela sua chave de API real
VLC_URL = "http://localhost:8080/requests/status.json"
VLC_PASS = "1234" # Senha configurada no VLC Lua HTTP

class VoteMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Votação - VLC")
        self.root.geometry("450x600") # Aumentado para caber o terminal de logs
        self.root.resizable(False, False)

        self.event_data = {}
        self.sessions_list = []
        self.selected_session = None
        self.monitoring = False
        self.last_chapter = -1

        self.setup_ui()
        self.fetch_sessions()

    def setup_ui(self):
        # Frame principal
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Seleção de Sessão
        ttk.Label(frame, text="Selecione a Sessão:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        self.session_var = tk.StringVar()
        self.session_cb = ttk.Combobox(frame, textvariable=self.session_var, state="readonly")
        self.session_cb.pack(fill=tk.X, pady=(0, 15))
        self.session_cb.bind("<<ComboboxSelected>>", self.on_session_select)

        # Informações do Evento
        self.lbl_event = ttk.Label(frame, text="Evento: Carregando...", font=("Arial", 12))
        self.lbl_event.pack(anchor=tk.W, pady=5)

        self.lbl_team = ttk.Label(frame, text="Equipe Atual: --", font=("Arial", 11, "bold"), foreground="blue")
        self.lbl_team.pack(anchor=tk.W, pady=5)

        # Labels de Progresso (API e VLC)
        self.lbl_progress = ttk.Label(frame, text="Votação (API): -- de --", font=("Arial", 11))
        self.lbl_progress.pack(anchor=tk.W, pady=5)

        self.lbl_vlc_chapter = ttk.Label(frame, text="VLC Capítulo: Aguardando...", font=("Arial", 11))
        self.lbl_vlc_chapter.pack(anchor=tk.W, pady=5)

        # Divisor visual
        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Botões de Ação
        self.btn_start_vote = ttk.Button(frame, text="▶ Iniciar Votação Manual", command=self.start_vote_api)
        self.btn_start_vote.pack(fill=tk.X, pady=(0, 5))

        self.btn_monitor = ttk.Button(frame, text="Iniciar Monitoramento VLC", command=self.toggle_monitoring)
        self.btn_monitor.pack(fill=tk.X, pady=(0, 0))
        
        # Status
        self.lbl_status = ttk.Label(frame, text="Status: Aguardando...", font=("Arial", 9), foreground="gray")
        self.lbl_status.pack(anchor=tk.W, pady=(10, 0))

        # ==========================================
        # NOVO: Terminal de Logs na Interface
        # ==========================================
        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(frame, text="Logs do Sistema:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        self.log_text = tk.Text(frame, height=8, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9), state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def log(self, message):
        """Imprime no console real e adiciona na caixa de texto da interface de forma segura (Thread-Safe)."""
        print(message) # Mantém no terminal por precaução
        
        def append_log():
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END) # Rola a barra para o final automaticamente
            self.log_text.config(state='disabled')
            
        self.root.after(0, append_log)

    def get_api_error_message(self, response):
        """Tenta extrair a mensagem de erro do JSON da API e joga no Log."""
        self.log(f"[API ERROR] HTTP {response.status_code} na rota {response.url}")
        self.log(f"[API RAW RESPONSE] {response.text}")
        self.log(f"[API HEADERS] {response.headers}")
        self.log(f"[API key] {API_KEY}")
        
        try:
            data = response.json()
            return data.get("error", data.get("message", f"HTTP {response.status_code}"))
        except Exception:
            return f"HTTP {response.status_code}"

    def fetch_sessions(self):
        """Busca as sessões na API e atualiza a interface."""
        try:
            headers = {"x-api-key": API_KEY}
            response = requests.get(f"{API_BASE_URL}/interactive-vote/event-sessions", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.event_data = data.get("event", {})
                self.sessions_list = data.get("sessions", [])
                
                # Atualiza o dropdown
                session_names = [s.get("configName", f"Sessão {s.get('id')}") for s in self.sessions_list]
                self.session_cb['values'] = session_names
                
                self.lbl_event.config(text=f"Evento: {self.event_data.get('name', 'Desconhecido')}")
                self.lbl_status.config(text="Status: Sessões carregadas.", foreground="green")
                self.log("Sessões sincronizadas com o backend.")
            else:
                error_msg = self.get_api_error_message(response)
                self.lbl_status.config(text=f"Erro API: {error_msg}", foreground="red")
        except Exception as e:
            self.lbl_status.config(text="Status: Erro ao conectar na API", foreground="red")
            self.log(f"Erro GET sessions: {e}")

    def on_session_select(self, event):
        """Atualiza a tela com os dados da sessão selecionada."""
        idx = self.session_cb.current()
        if idx >= 0:
            self.selected_session = self.sessions_list[idx]
            self.update_labels_from_session()
            self.log(f"Sessão selecionada: {self.selected_session.get('configName', 'Desconhecida')}")

    def update_labels_from_session(self):
        if self.selected_session:
            team_name = self.selected_session.get("currentTeamName", "--")
            current_idx = self.selected_session.get("currentIndex", "?")
            total_teams = self.selected_session.get("totalTeams", "?")
            
            self.lbl_team.config(text=f"Equipe Atual: {team_name}")
            self.lbl_progress.config(text=f"Votação (API): {current_idx} de {total_teams}")

    def toggle_monitoring(self):
        """Inicia ou para a thread do VLC."""
        if not self.selected_session:
            messagebox.showwarning("Aviso", "Selecione uma sessão primeiro!")
            return

        if self.monitoring:
            self.monitoring = False
            self.btn_monitor.config(text="Iniciar Monitoramento VLC")
            self.lbl_status.config(text="Status: Monitoramento Parado.", foreground="gray")
            self.log("Monitoramento do VLC parado.")
        else:
            self.monitoring = True
            self.last_chapter = -1 # Reseta o estado do capítulo sempre que iniciar o monitor
            self.btn_monitor.config(text="Parar Monitoramento")
            self.lbl_status.config(text="Status: Monitorando VLC...", foreground="green")
            self.log("Iniciando varredura do VLC...")
            
            # Inicia thread em background
            threading.Thread(target=self.vlc_monitor_thread, daemon=True).start()

    def vlc_monitor_thread(self):
        """Loop que roda em background checando o VLC."""
        while self.monitoring:
            try:
                response = requests.get(VLC_URL, auth=("", VLC_PASS), timeout=2)
                
                if response.status_code == 200:
                    vlc_data = response.json()
                    
                    info = vlc_data.get("information", {})
                    current_chapter = info.get("chapter", -1)
                    
                    chapters_list = info.get("chapters", [])
                    total_chapters = len(chapters_list)
                    
                    if current_chapter != -1:
                        display_chapter = current_chapter + 1
                        self.root.after(0, lambda c=display_chapter, t=total_chapters: 
                                        self.lbl_vlc_chapter.config(text=f"VLC Capítulo: {c} de {t}"))
                        
                        if current_chapter != self.last_chapter:
                            self.log(f"Mudança de capítulo detectada pelo VLC: Capítulo {current_chapter}")
                            
                            if self.last_chapter == -1 and current_chapter == 0:
                                self.log("Início do vídeo detectado! Auto-iniciando votação...")
                                self.start_vote_api()
                            elif self.last_chapter != -1:
                                self.log("Avançando para a próxima equipe...")
                                self.advance_team_api()
                                
                            self.last_chapter = current_chapter
            except requests.exceptions.RequestException:
                self.root.after(0, lambda: self.lbl_vlc_chapter.config(text="VLC: Desconectado/Aguardando..."))
            
            time.sleep(1)

    def start_vote_api(self):
        """Faz o POST para Iniciar a votação."""
        if not self.selected_session or not self.event_data:
            messagebox.showwarning("Aviso", "Selecione uma sessão (e aguarde carregar o evento) primeiro!")
            return

        session_id = self.selected_session.get("id")
        headers = {"x-api-key": API_KEY}
        
        try:
            self.log("Enviando requisição START para a API...")
            url = f"{API_BASE_URL}/interactive-vote/api/{session_id}/start"
            response = requests.post(url, headers=headers)
            
            if response.status_code == 200:
                self.root.after(0, lambda: self.lbl_status.config(text="Status: Votação Iniciada com Sucesso!", foreground="green"))
                self.log("✅ Votação iniciada com sucesso.")
                self.root.after(0, self.fetch_sessions_and_update_ui)
            else:
                error_msg = self.get_api_error_message(response)
                self.root.after(0, lambda msg=error_msg: self.lbl_status.config(text=f"Erro: {msg}", foreground="red"))
        except Exception as e:
            self.root.after(0, lambda: self.lbl_status.config(text="Erro de conexão ao iniciar", foreground="red"))
            self.log(f"Erro POST start: {e}")

    def advance_team_api(self):
        """Faz o POST para avançar a equipe e atualiza a UI."""
        if not self.selected_session or not self.event_data:
            return

        session_id = self.selected_session.get("id")
        event_id = self.event_data.get("id")
        
        headers = {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "chapterName": "", 
            "eventId": event_id
        }
        
        try:
            self.log("Enviando requisição NEXT para a API...")
            url = f"{API_BASE_URL}/interactive-vote/api/{session_id}/next"
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ended"):
                    self.root.after(0, lambda: self.lbl_status.config(text="Status: Votação Encerrada!", foreground="blue"))
                    self.log("🏆 Votação reportada como encerrada pela API.")
                    self.monitoring = False
                    self.root.after(0, lambda: self.btn_monitor.config(text="Iniciar Monitoramento VLC"))
                else:
                    self.root.after(0, lambda: self.lbl_status.config(text="Status: Avançou com sucesso!", foreground="green"))
                    self.log("✅ Equipe avançada com sucesso.")
                    self.root.after(0, self.fetch_sessions_and_update_ui)
            else:
                error_msg = self.get_api_error_message(response)
                self.root.after(0, lambda msg=error_msg: self.lbl_status.config(text=f"Erro ao avançar: {msg}", foreground="red"))
        except Exception as e:
            self.root.after(0, lambda: self.lbl_status.config(text="Erro de conexão ao avançar equipe", foreground="red"))
            self.log(f"Erro POST next: {e}")

    def fetch_sessions_and_update_ui(self):
        """Busca os dados atualizados pós avanço/início."""
        self.fetch_sessions()
        
        if self.selected_session:
            session_id = self.selected_session.get("id")
            for s in self.sessions_list:
                if s.get("id") == session_id:
                    self.selected_session = s
                    self.update_labels_from_session()
                    break

if __name__ == "__main__":
    root = tk.Tk()
    app = VoteMonitorApp(root)
    root.mainloop()