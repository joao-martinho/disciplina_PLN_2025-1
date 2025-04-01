import os
import re
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import ttk, messagebox, scrolledtext, font
from urllib.parse import urlparse

import pyperclip
import requests
from bs4 import BeautifulSoup
from collections import Counter


class BibleScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extração de Textos Bíblicos")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        self.root.minsize(900, 700)

        # Configuração de estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Cores principais
        self.primary_color = "#01627E"
        self.secondary_color = "#f0f0f0"
        self.text_color = "#333333"
        self.success_color = "#4CAF50"
        self.error_color = "#F44336"

        # Configurar estilos
        self.style.configure('TFrame', background=self.secondary_color)
        self.style.configure('TLabel', background=self.secondary_color,
                             font=('Segoe UI', 10), foreground=self.text_color)
        self.style.configure('TButton', font=('Segoe UI', 10), padding=8,
                             background=self.primary_color, foreground='white')
        self.style.map('TButton',
                       background=[('active', '#0288D1'), ('pressed', '#005B7F')])
        self.style.configure('Header.TLabel', font=('Segoe UI', 18, 'bold'),
                             foreground=self.primary_color)
        self.style.configure('Subtitle.TLabel', font=('Segoe UI', 10, 'italic'),
                             foreground="#666666")
        self.style.configure('Success.TLabel', foreground=self.success_color)
        self.style.configure('Error.TLabel', foreground=self.error_color)
        self.style.configure('TEntry', padding=5, font=('Segoe UI', 10))

        # Configurar fundo da janela principal
        self.root.configure(bg=self.secondary_color)

        # Cabeçalho
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(pady=(10, 5), padx=10, fill='x')

        self.title_label = ttk.Label(
            self.header_frame,
            text="Extração de Textos Bíblicos",
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
        self.main_frame.pack(pady=5, padx=10, fill='both', expand=True)

        # Frame de entrada
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill='x', pady=(5, 10))

        ttk.Label(
            self.input_frame,
            text="URL do texto bíblico (ex: https://www.bibliaonline.com.br/nvi/gn/1):"
        ).pack(anchor='w')

        self.url_entry = ttk.Entry(self.input_frame, width=80)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))

        self.fetch_button = ttk.Button(
            self.input_frame,
            text="Extrair Texto",
            command=self.fetch_bible_text,
            style='TButton'
        )
        self.fetch_button.pack(side='left')

        # Frame de status
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill='x', pady=(0, 10))

        self.status_label = ttk.Label(self.status_frame, text="Pronto para começar.")
        self.status_label.pack(anchor='w')

        # Frame de resultados
        self.result_frame = ttk.Frame(self.main_frame)
        self.result_frame.pack(fill='both', expand=True)

        # Notebook para abas de resultados
        self.result_notebook = ttk.Notebook(self.result_frame)
        self.result_notebook.pack(fill='both', expand=True)

        # Aba de texto completo
        self.text_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.text_tab, text='Texto Completo')

        ttk.Label(self.text_tab, text="Texto Extraído:").pack(anchor='w')

        # Configurar fonte com espaçamento melhor
        text_font = font.Font(family='Segoe UI', size=11)

        self.result_text = scrolledtext.ScrolledText(
            self.text_tab,
            wrap=tk.WORD,
            font=text_font,
            padx=10,
            pady=10,
            bg='white',
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.primary_color,
            selectforeground='white'
        )
        self.result_text.pack(fill='both', expand=True)

        # Adicionar tags para formatação
        self.result_text.tag_configure('header', font=('Segoe UI', 12, 'bold'))
        self.result_text.tag_configure('verse', font=('Segoe UI', 11))
        self.result_text.tag_configure('verse_number', font=('Segoe UI', 11, 'bold'), foreground=self.primary_color)

        # Aba de palavras-chave
        self.keywords_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.keywords_tab, text='Palavras Importantes')

        ttk.Label(self.keywords_tab, text="Palavras mais relevantes (excluindo conectivos):").pack(anchor='w')

        self.keywords_text = scrolledtext.ScrolledText(
            self.keywords_tab,
            wrap=tk.WORD,
            font=text_font,
            padx=10,
            pady=10,
            bg='white',
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.primary_color,
            selectforeground='white'
        )
        self.keywords_text.pack(fill='both', expand=True)

        # Frame de rodapé
        self.footer_frame = ttk.Frame(self.main_frame)
        self.footer_frame.pack(fill='x', pady=(10, 0))

        self.save_button = ttk.Button(
            self.footer_frame,
            text="Salvar em Arquivo",
            command=self.save_to_file,
            style='TButton',
            state='disabled'
        )
        self.save_button.pack(side='left', padx=(0, 10))

        self.copy_button = ttk.Button(
            self.footer_frame,
            text="Copiar para Área de Transferência",
            command=self.copy_to_clipboard,
            style='TButton',
            state='disabled'
        )
        self.copy_button.pack(side='left', padx=(0, 10))

        self.clear_button = ttk.Button(
            self.footer_frame,
            text="Limpar",
            command=self.clear_results,
            style='TButton'
        )
        self.clear_button.pack(side='left')

        # Barra de progresso
        self.progress = ttk.Progressbar(
            self.footer_frame,
            orient='horizontal',
            mode='determinate',
            length=200
        )
        self.progress.pack(side='right')

        # Menu
        self.menu_bar = tk.Menu(self.root)

        # Menu Arquivo
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.secondary_color, fg=self.text_color)
        self.file_menu.add_command(label="Salvar", command=self.save_to_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Sair", command=self.root.quit)
        self.menu_bar.add_cascade(label="Arquivo", menu=self.file_menu)

        # Menu Editar
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.secondary_color, fg=self.text_color)
        self.edit_menu.add_command(label="Copiar", command=self.copy_to_clipboard)
        self.edit_menu.add_command(label="Limpar", command=self.clear_results)
        self.menu_bar.add_cascade(label="Editar", menu=self.edit_menu)

        # Menu Ajuda
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.secondary_color, fg=self.text_color)
        self.help_menu.add_command(label="Sobre", command=self.show_about)
        self.help_menu.add_command(label="Documentação", command=self.open_docs)
        self.menu_bar.add_cascade(label="Ajuda", menu=self.help_menu)

        self.root.config(menu=self.menu_bar)

        # Dicas de uso
        self.url_entry.insert(0, "https://www.bibliaonline.com.br/nvi/gn/1")

        # Configurar atalhos
        self.root.bind('<Control-s>', lambda e: self.save_to_file())
        self.root.bind('<Control-c>', lambda e: self.copy_to_clipboard())

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
            self.progress['value'] = 20
            self.root.update()

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            self.update_status("Processando conteúdo...", "black")
            self.progress['value'] = 50
            self.root.update()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extrai metadados da URL
            path_parts = [p for p in parsed_url.path.split('/') if p]
            translation = path_parts[-3] if len(path_parts) >= 3 else "desconhecida"
            book = path_parts[-2] if len(path_parts) >= 2 else "desconhecido"
            chapter = path_parts[-1] if len(path_parts) >= 1 else "desconhecido"

            # Extrai o texto bíblico
            text_content = self.extract_bible_text(soup)

            if not text_content:
                raise ValueError("Não foi possível identificar o texto bíblico na página.")

            self.result_text.delete(1.0, tk.END)
            self.keywords_text.delete(1.0, tk.END)

            # Insere cabeçalho formatado
            self.result_text.insert(tk.END, f"TRADUÇÃO: {translation.upper()}\n", 'header')
            self.result_text.insert(tk.END, f"LIVRO: {book.upper()}\n", 'header')
            self.result_text.insert(tk.END, f"CAPÍTULO: {chapter}\n\n", 'header')

            # Insere versículos formatados
            full_text = ""
            for verse in text_content:
                self.result_text.insert(tk.END, f"{verse['number']} ", 'verse_number')
                self.result_text.insert(tk.END, f"{verse['text']}\n\n", 'verse')
                full_text += f" {verse['text']}"

            # Processa as palavras-chave
            keywords = self.extract_keywords(full_text)
            self.keywords_text.insert(tk.END, "Palavras mais frequentes (excluindo conectivos):\n\n", 'header')
            
            for word, count in keywords.most_common(50):  # Mostra as 50 palavras mais frequentes
                self.keywords_text.insert(tk.END, f"{word}: {count}\n")

            self.update_status(f"Texto extraído com sucesso de {parsed_url.netloc}!", self.success_color)
            self.progress['value'] = 100
            self.save_button.config(state='normal')
            self.copy_button.config(state='normal')

        except requests.exceptions.RequestException as e:
            self.show_error(f"Erro ao acessar a URL: {str(e)}")
            self.progress['value'] = 0
        except ValueError as e:
            self.show_error(str(e))
            self.progress['value'] = 0
        except Exception as e:
            self.show_error(f"Erro inesperado: {str(e)}")
            self.progress['value'] = 0
        finally:
            self.root.after(2000, lambda: self.progress.config(value=0))

    def extract_bible_text(self, soup):
        """Extrai o texto bíblico da página com formatação melhorada"""
        verses = []

        # Estratégia 1: Procurar por versículos com números
        verse_elements = soup.find_all(['p', 'div', 'span'], class_=re.compile(r'verse|versicle|versiculo', re.I))

        # Estratégia 2: Procurar por números de versículos (1, 2, 3...)
        if not verse_elements:
            verse_elements = soup.find_all(text=re.compile(r'^\d+\s'))

        # Estratégia 3: Procurar em áreas de conteúdo principal
        if not verse_elements:
            content = soup.find(['article', 'main', 'div'], class_=re.compile(r'content|text|chapter', re.I))
            if content:
                verse_elements = content.find_all(['p', 'div'])

        # Se nenhuma estratégia funcionar, retorna todo o texto da página como um único "versículo"
        if not verse_elements:
            full_text = soup.get_text(separator='\n', strip=True)
            return [{'number': '1', 'text': full_text}]

        # Processa os versículos encontrados
        for element in verse_elements:
            verse_text = element.get_text(strip=True)

            # Extrai número do versículo
            verse_match = re.match(r'^(\d+)\s*(.*)', verse_text)
            if verse_match:
                verse_number = verse_match.group(1)
                verse_content = verse_match.group(2)
            else:
                verse_number = "?"
                verse_content = verse_text

            # Limpa espaços extras e quebras de linha
            verse_content = ' '.join(verse_content.split())

            verses.append({
                'number': verse_number,
                'text': verse_content
            })

        return verses

    def extract_keywords(self, text):
        """Extrai palavras-chave importantes, excluindo conectivos comuns"""
        # Lista de palavras de conexão/artigos/preposições para excluir (em português)
        stopwords = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'de', 'do', 'da', 'dos', 'das',
            'em', 'no', 'na', 'nos', 'nas', 'por', 'pelo', 'pela', 'pelos', 'pelas', 'para',
            'com', 'como', 'que', 'e', 'ou', 'se', 'mas', 'porque', 'pois', 'quando', 'onde',
            'como', 'qual', 'quais', 'quem', 'cujo', 'cuja', 'cujos', 'cujas', 'este', 'esta',
            'estes', 'estas', 'esse', 'essa', 'esses', 'essas', 'aquele', 'aquela', 'aqueles',
            'aquelas', 'não', 'sim', 'sem', 'sob', 'sobre', 'entre', 'até', 'para', 'por', 'pelo',
            'pela', 'pelos', 'pelas', 'meu', 'minha', 'meus', 'minhas', 'teu', 'tua', 'teus',
            'tuas', 'seu', 'sua', 'seus', 'suas', 'nosso', 'nossa', 'nossos', 'nossas', 'vosso',
            'vossa', 'vossos', 'vossas', 'lhe', 'lhes', 'lho', 'lha', 'lhos', 'lhas', 'lhe', 'lhes',
            'se', 'si', 'consigo', 'eu', 'tu', 'ele', 'ela', 'nós', 'vós', 'eles', 'elas', 'me',
            'te', 'o', 'a', 'lhe', 'nos', 'vos', 'os', 'as', 'lhes', 'mim', 'ti', 'ele', 'ela',
            'nós', 'vós', 'eles', 'elas', 'comigo', 'contigo', 'conosco', 'convosco', 'connosco',
            'contigo', 'consigo', 'quem', 'que', 'cujo', 'cuja', 'cujos', 'cujas', 'onde', 'aonde',
            'quando', 'como', 'porque', 'porquê', 'pois', 'então', 'assim', 'logo', 'portanto',
            'também', 'tampouco', 'além', 'acima', 'abaixo', 'antes', 'depois', 'agora', 'ainda',
            'já', 'sempre', 'nunca', 'jamais', 'breve', 'cedo', 'tarde', 'hoje', 'ontem', 'amanhã',
            'logo', 'aqui', 'ali', 'lá', 'acolá', 'cá', 'algures', 'nenhures', 'outrora', 'doravante',
            'sim', 'não', 'talvez', 'certamente', 'efetivamente', 'realmente', 'verdadeiramente',
            'absolutamente', 'bastante', 'demais', 'muito', 'pouco', 'quanto', 'tanto', 'quão',
            'quase', 'só', 'apenas', 'exatamente', 'justamente', 'precisamente', 'unicamente',
            'tão', 'tanto', 'quanto', 'assim', 'bem', 'mal', 'melhor', 'pior', 'ótimo', 'péssimo',
            'grande', 'pequeno', 'longe', 'perto', 'alto', 'baixo', 'rápido', 'devagar', 'ligeiro',
            'lento', 'fácil', 'difícil', 'leve', 'pesado', 'forte', 'fraco', 'duro', 'mole', 'seco',
            'molhado', 'quente', 'frio', 'novo', 'velho', 'jovem', 'antigo', 'moderno', 'bonito',
            'feio', 'bom', 'mau', 'feliz', 'triste', 'alegre', 'contente', 'descontente', 'satisfeito',
            'insatisfeito', 'cheio', 'vazio', 'rico', 'pobre', 'caro', 'barato', 'caro', 'barato',
            'claro', 'escuro', 'limpo', 'sujo', 'cheio', 'vazio', 'pesado', 'leve', 'forte', 'fraco',
            'rápido', 'lento', 'fácil', 'difícil', 'simples', 'complexo', 'direito', 'esquerdo',
            'superior', 'inferior', 'central', 'lateral', 'frontal', 'traseiro', 'interno', 'externo',
            'público', 'privado', 'nacional', 'internacional', 'local', 'global', 'urbano', 'rural',
            'natural', 'artificial', 'real', 'virtual', 'positivo', 'negativo', 'ativo', 'passivo',
            'principal', 'secundário', 'terciário', 'primário', 'final', 'inicial', 'básico', 'avançado',
            'geral', 'específico', 'comum', 'raro', 'normal', 'anormal', 'usual', 'inusual', 'frequente',
            'infrequente', 'constante', 'variável', 'fixo', 'móvel', 'estável', 'instável', 'seguro',
            'perigoso', 'útil', 'inútil', 'necessário', 'desnecessário', 'importante', 'irrelevante',
            'urgente', 'tranquilo', 'calmo', 'agitado', 'barulhento', 'silencioso', 'suave', 'áspero',
            'liso', 'rugoso', 'macio', 'duro', 'flexível', 'rígido', 'elástico', 'plástico', 'metálico',
            'madeira', 'vidro', 'plástico', 'tecido', 'papel', 'pedra', 'concreto', 'argila', 'cerâmica',
            'porcelana', 'borracha', 'couro', 'espuma', 'algodão', 'seda', 'linho', 'lã', 'náilon',
            'poliéster', 'acrílico', 'vinil', 'pvc', 'ferro', 'aço', 'cobre', 'bronze', 'latão',
            'ouro', 'prata', 'platina', 'paládio', 'níquel', 'zinco', 'chumbo', 'estanho', 'alumínio',
            'titânio', 'tungstênio', 'mercúrio', 'magnésio', 'cálcio', 'potássio', 'sódio', 'lítio',
            'berílio', 'boro', 'carbono', 'nitrogênio', 'oxigênio', 'flúor', 'neônio', 'hidrogênio',
            'hélio', 'argônio', 'criptônio', 'xenônio', 'radônio', 'urânio', 'plutônio', 'tório',
            'rádio', 'polônio', 'actínio', 'protactínio', 'tório', 'urânio', 'neptúnio', 'plutônio',
            'amerício', 'cúrio', 'berquélio', 'califórnio', 'einstênio', 'férmio', 'mendelévio',
            'nobélio', 'laurêncio', 'rutherfórdio', 'dúbnio', 'seabórgio', 'bóhrio', 'hássio',
            'meitnério', 'darmstádio', 'roentgênio', 'copernício', 'nihônio', 'fleróvio', 'moscóvio',
            'livermório', 'tenesso', 'oganessônio'
        }

        # Tokeniza o texto em palavras
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filtra palavras com mais de 3 caracteres que não estão na lista de stopwords
        keywords = [word for word in words if len(word) > 3 and word not in stopwords]
        
        # Conta a frequência de cada palavra
        return Counter(keywords)

    def save_to_file(self):
        content = self.result_text.get(1.0, tk.END)
        if not content.strip():
            self.show_error("Nenhum conteúdo para salvar.")
            return

        try:
            # Cria diretório de saída se não existir
            os.makedirs('output', exist_ok=True)

            # Gera nome de arquivo com base na data, hora e livro/capítulo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Tenta extrair livro e capítulo do texto
            book = "biblia"
            chapter = "texto"

            # Procura por padrões no texto
            book_match = re.search(r'LIVRO:\s*(\w+)', content, re.I)
            chapter_match = re.search(r'CAPÍTULO:\s*(\w+)', content, re.I)

            if book_match:
                book = book_match.group(1).lower()
            if chapter_match:
                chapter = chapter_match.group(1).lower()

            filename = f"output/{book}_cap{chapter}_{timestamp}.txt"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            self.update_status(f"Texto salvo com sucesso em {filename}", self.success_color)
            messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso em:\n{os.path.abspath(filename)}")
        except Exception as e:
            self.show_error(f"Erro ao salvar arquivo: {str(e)}")

    def copy_to_clipboard(self):
        content = self.result_text.get(1.0, tk.END)
        if not content.strip():
            self.show_error("Nenhum conteúdo para copiar.")
            return

        try:
            pyperclip.copy(content)
            self.update_status("Texto copiado para a área de transferência!", self.success_color)
        except Exception as e:
            self.show_error(f"Erro ao copiar para área de transferência: {str(e)}")

    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
        self.keywords_text.delete(1.0, tk.END)
        self.update_status("Pronto para começar.", "black")
        self.save_button.config(state='disabled')
        self.copy_button.config(state='disabled')

    def update_status(self, message, color="black"):
        self.status_label.config(text=message, foreground=color)

    def show_error(self, message):
        self.update_status(f"Erro: {message}", self.error_color)
        messagebox.showerror("Erro", message)

    def show_about(self):
        about_text = """BibleScraper v2.0

Uma ferramenta profissional para extração de textos bíblicos de sites.

Recursos:
- Extração de textos de diversas traduções
- Interface moderna e intuitiva
- Formatação automática dos textos
- Tratamento robusto de erros
- Opções de salvamento e cópia
- Atalhos de teclado
- Análise de palavras-chave

Desenvolvido com Python, Tkinter e BeautifulSoup.

© 2025 Extração de Textos Bíblicos - Todos os direitos reservados"""
        messagebox.showinfo("Sobre", about_text)

    def open_docs(self):
        docs_url = "https://github.com/biblescraper/docs"
        try:
            webbrowser.open_new(docs_url)
        except:
            self.show_error("Não foi possível abrir a documentação.")


if __name__ == "__main__":
    root = tk.Tk()

    # Centralizar a janela
    window_width = 1000
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    app = BibleScraperApp(root)
    root.mainloop()
