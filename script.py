import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import webbrowser
from datetime import datetime
import os

class BibleScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BibleScraper - Extração de Textos Bíblicos")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        
        # Configuração de estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Arial', 10, 'italic'))
        self.style.configure('Success.TLabel', foreground='green')
        self.style.configure('Error.TLabel', foreground='red')
        
        # Cabeçalho
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(pady=10, padx=10, fill='x')
        
        self.title_label = ttk.Label(
            self.header_frame, 
            text="BibleScraper", 
            style='Header.TLabel'
        )
        self.title_label.pack()
        
        self.subtitle_label = ttk.Label(
            self.header_frame, 
            text="Ferramenta profissional para extração de textos bíblicos de sites", 
            style='Subtitle.TLabel'
        )
        self.subtitle_label.pack()
        
        # Frame principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Frame de entrada
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill='x', pady=5)
        
        ttk.Label(
            self.input_frame, 
            text="URL do texto bíblico (formato: https://site.com/traducao/livro/capitulo):"
        ).pack(anchor='w')
        
        self.url_entry = ttk.Entry(self.input_frame, width=70)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.fetch_button = ttk.Button(
            self.input_frame, 
            text="Extrair Texto", 
            command=self.fetch_bible_text
        )
        self.fetch_button.pack(side='left')
        
        # Frame de status
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill='x', pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Pronto para começar.")
        self.status_label.pack(anchor='w')
        
        # Frame de resultados
        self.result_frame = ttk.Frame(self.main_frame)
        self.result_frame.pack(fill='both', expand=True)
        
        ttk.Label(self.result_frame, text="Texto Extraído:").pack(anchor='w')
        
        self.result_text = scrolledtext.ScrolledText(
            self.result_frame, 
            wrap=tk.WORD, 
            font=('Arial', 11),
            padx=10,
            pady=10
        )
        self.result_text.pack(fill='both', expand=True)
        
        # Frame de rodapé
        self.footer_frame = ttk.Frame(self.main_frame)
        self.footer_frame.pack(fill='x', pady=10)
        
        self.save_button = ttk.Button(
            self.footer_frame, 
            text="Salvar em Arquivo", 
            command=self.save_to_file,
            state='disabled'
        )
        self.save_button.pack(side='left', padx=(0, 5))
        
        self.copy_button = ttk.Button(
            self.footer_frame, 
            text="Copiar para Área de Transferência", 
            command=self.copy_to_clipboard,
            state='disabled'
        )
        self.copy_button.pack(side='left', padx=(0, 5))
        
        self.clear_button = ttk.Button(
            self.footer_frame, 
            text="Limpar", 
            command=self.clear_results
        )
        self.clear_button.pack(side='left')
        
        # Menu
        self.menu_bar = tk.Menu(self.root)
        
        # Menu Arquivo
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Sair", command=self.root.quit)
        self.menu_bar.add_cascade(label="Arquivo", menu=self.file_menu)
        
        # Menu Ajuda
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Sobre", command=self.show_about)
        self.help_menu.add_command(label="Documentação", command=self.open_docs)
        self.menu_bar.add_cascade(label="Ajuda", menu=self.help_menu)
        
        self.root.config(menu=self.menu_bar)
        
        # Dicas de uso
        self.url_entry.insert(0, "https://www.bibliaonline.com.br/nvi/gn/1")
        
    def fetch_bible_text(self):
        url = self.url_entry.get().strip()
        
        if not url:
            self.show_error("Por favor, insira uma URL válida.")
            return
        
        try:
            # Validação básica da URL
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("URL inválida")
                
            # Verifica se a URL segue o padrão esperado
            if not re.search(r'/.+/.+/.+', parsed_url.path):
                raise ValueError("URL não segue o formato esperado: /traducao/livro/capitulo")
                
            self.update_status(f"Conectando a {parsed_url.netloc}...", "black")
            self.root.update()
            
            headers = {
                'User-Agent': 'BibleScraper/1.0 (+https://github.com/biblescraper)'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            self.update_status("Processando conteúdo...", "black")
            self.root.update()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tenta encontrar o texto bíblico - esta parte pode precisar de ajustes para sites específicos
            # Aqui usamos uma abordagem genérica que pode ser adaptada
            text_content = self.extract_bible_text(soup)
            
            if not text_content:
                raise ValueError("Não foi possível identificar o texto bíblico na página.")
                
            # Extrai metadados da URL
            path_parts = parsed_url.path.split('/')
            translation = path_parts[-3] if len(path_parts) >= 3 else "desconhecida"
            book = path_parts[-2] if len(path_parts) >= 2 else "desconhecido"
            chapter = path_parts[-1] if len(path_parts) >= 1 else "desconhecido"
            
            # Formata o resultado
            result = f"TRADUÇÃO: {translation.upper()}\n"
            result += f"LIVRO: {book.upper()}\n"
            result += f"CAPÍTULO: {chapter}\n\n"
            result += text_content
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            
            self.update_status(f"Texto extraído com sucesso de {parsed_url.netloc}!", "green")
            self.save_button.config(state='normal')
            self.copy_button.config(state='normal')
            
        except requests.exceptions.RequestException as e:
            self.show_error(f"Erro ao acessar a URL: {str(e)}")
        except ValueError as e:
            self.show_error(str(e))
        except Exception as e:
            self.show_error(f"Erro inesperado: {str(e)}")
    
    def extract_bible_text(self, soup):
        """Extrai o texto bíblico da página, com tentativas de diferentes estratégias"""
        # Estratégia 1: Procurar por tags comuns de versículos
        verses = soup.find_all(['p', 'div', 'span'], class_=re.compile(r'verse|versicle|versiculo', re.I))
        
        # Estratégia 2: Procurar por números de versículos (1, 2, 3...)
        if not verses:
            verses = soup.find_all(text=re.compile(r'^\d+\s'))
            
        # Estratégia 3: Procurar em áreas de conteúdo principal
        if not verses:
            content = soup.find(['article', 'main', 'div'], class_=re.compile(r'content|text|chapter', re.I))
            if content:
                verses = content.find_all(['p', 'div'])
                
        # Se nenhuma estratégia funcionar, retorna todo o texto da página
        if not verses:
            return soup.get_text(separator='\n', strip=True)
            
        # Processa os versículos encontrados
        text = ""
        for verse in verses:
            verse_text = verse.get_text(separator=' ', strip=True)
            # Remove possíveis números de versículo no início
            verse_text = re.sub(r'^\d+\s', '', verse_text)
            text += verse_text + "\n\n"
            
        return text.strip()
    
    def save_to_file(self):
        content = self.result_text.get(1.0, tk.END)
        if not content.strip():
            self.show_error("Nenhum conteúdo para salvar.")
            return
            
        try:
            # Cria diretório de saída se não existir
            os.makedirs('output', exist_ok=True)
            
            # Gera nome de arquivo com base na data e hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/bible_text_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.update_status(f"Texto salvo com sucesso em {filename}", "green")
            messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso em:\n{os.path.abspath(filename)}")
        except Exception as e:
            self.show_error(f"Erro ao salvar arquivo: {str(e)}")
    
    def copy_to_clipboard(self):
        content = self.result_text.get(1.0, tk.END)
        if not content.strip():
            self.show_error("Nenhum conteúdo para copiar.")
            return
            
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.update_status("Texto copiado para a área de transferência!", "green")
        except Exception as e:
            self.show_error(f"Erro ao copiar para área de transferência: {str(e)}")
    
    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
        self.update_status("Pronto para começar.", "black")
        self.save_button.config(state='disabled')
        self.copy_button.config(state='disabled')
    
    def update_status(self, message, color="black"):
        self.status_label.config(text=message, foreground=color)
    
    def show_error(self, message):
        self.update_status(f"Erro: {message}", "red")
        messagebox.showerror("Erro", message)
    
    def show_about(self):
        about_text = """BibleScraper v1.0

Uma ferramenta profissional para extração de textos bíblicos de sites.

Recursos:
- Extração de textos de diversas traduções
- Interface amigável e intuitiva
- Tratamento robusto de erros
- Opções de salvamento e cópia

Desenvolvido com Python, Tkinter e BeautifulSoup."""
        messagebox.showinfo("Sobre", about_text)
    
    def open_docs(self):
        docs_url = "https://github.com/biblescraper/docs"
        try:
            webbrowser.open_new(docs_url)
        except:
            self.show_error("Não foi possível abrir a documentação.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BibleScraperApp(root)
    root.mainloop()