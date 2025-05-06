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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import numpy as np
import spacy
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class BibleScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extração de Textos Bíblicos")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)

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
                             font=('Segoe UI', 9), foreground=self.text_color)
        self.style.configure('TButton', font=('Segoe UI', 9), padding=6,
                             background=self.primary_color, foreground='white')
        self.style.map('TButton',
                       background=[('active', '#0288D1'), ('pressed', '#005B7F')])
        self.style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'),
                             foreground=self.primary_color)
        self.style.configure('Subtitle.TLabel', font=('Segoe UI', 9, 'italic'),
                             foreground="#666666")
        self.style.configure('Success.TLabel', foreground=self.success_color)
        self.style.configure('Error.TLabel', foreground=self.error_color)
        self.style.configure('TEntry', padding=4, font=('Segoe UI', 9))

        # Configurar estilo da barra de progresso
        self.style.configure("green.Horizontal.TProgressbar",
                             troughcolor=self.secondary_color,
                             background=self.success_color,
                             lightcolor=self.success_color,
                             darkcolor=self.success_color)

        # Configurar fundo da janela principal
        self.root.configure(bg=self.secondary_color)

        # Cabeçalho
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(pady=(5, 3), padx=5, fill='x')

        self.title_label = ttk.Label(
            self.header_frame,
            text="Extração de Textos Bíblicos",
            style='Header.TLabel'
        )
        self.title_label.pack()

        self.subtitle_label = ttk.Label(
            self.header_frame,
            text="Ferramenta para extração e análise de textos bíblicos",
            style='Subtitle.TLabel'
        )
        self.subtitle_label.pack()

        # Frame principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(pady=3, padx=5, fill='both', expand=True)

        # Frame de entrada
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill='x', pady=(3, 5))

        ttk.Label(
            self.input_frame,
            text="URL do texto bíblico (ex: https://www.bibliaonline.com.br/nvi/gn/1):"
        ).pack(anchor='w')

        self.url_frame = ttk.Frame(self.input_frame)
        self.url_frame.pack(fill='x', expand=True)

        self.url_entry = ttk.Entry(self.url_frame)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        self.fetch_button = ttk.Button(
            self.url_frame,
            text="Extrair",
            command=self.fetch_bible_text,
            style='TButton',
            width=10
        )
        self.fetch_button.pack(side='left')

        # Frame de status
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill='x', pady=(0, 5))

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

        text_font = font.Font(family='Segoe UI', size=10)

        self.result_text = scrolledtext.ScrolledText(
            self.text_tab,
            wrap=tk.WORD,
            font=text_font,
            padx=8,
            pady=8,
            bg='white',
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.primary_color,
            selectforeground='white',
            state='disabled'
        )
        self.result_text.pack(fill='both', expand=True)

        # Adicionar tags para formatação
        self.result_text.tag_configure('header', font=('Segoe UI', 11, 'bold'))
        self.result_text.tag_configure('verse', font=('Segoe UI', 10))
        self.result_text.tag_configure('verse_number', font=('Segoe UI', 10, 'bold'), foreground=self.primary_color)

        # Aba de palavras-chave
        self.keywords_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.keywords_tab, text='Palavras Importantes')

        ttk.Label(self.keywords_tab, text="Palavras mais relevantes (excluindo conectivos):").pack(anchor='w')

        self.keywords_text = scrolledtext.ScrolledText(
            self.keywords_tab,
            wrap=tk.WORD,
            font=text_font,
            padx=8,
            pady=8,
            bg='white',
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.primary_color,
            selectforeground='white',
            state='disabled'
        )
        self.keywords_text.pack(fill='both', expand=True)

        # Aba de clusterização
        self.cluster_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.cluster_tab, text='Análise de Tópicos')

        ttk.Label(self.cluster_tab, text="Agrupamento de versículos por similaridade:").pack(anchor='w')

        self.cluster_text = scrolledtext.ScrolledText(
            self.cluster_tab,
            wrap=tk.WORD,
            font=text_font,
            padx=8,
            pady=8,
            bg='white',
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.primary_color,
            selectforeground='white',
            state='disabled'
        )
        self.cluster_text.pack(fill='both', expand=True)

        # Aba de entidades
        self.entities_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.entities_tab, text='Análise de Entidades')

        ttk.Label(self.entities_tab, text="Entidades e Atributos Linguísticos:").pack(anchor='w')

        self.entities_text = scrolledtext.ScrolledText(
            self.entities_tab,
            wrap=tk.WORD,
            font=text_font,
            padx=8,
            pady=8,
            bg='white',
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.primary_color,
            selectforeground='white',
            state='disabled'
        )
        self.entities_text.pack(fill='both', expand=True)

        # Aba de sumarização
        self.summary_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.summary_tab, text='Sumarização')

        ttk.Label(self.summary_tab, text="Sumarização Extrativa e Palavras-chave:").pack(anchor='w')

        self.summary_text = scrolledtext.ScrolledText(
            self.summary_tab,
            wrap=tk.WORD,
            font=text_font,
            padx=8,
            pady=8,
            bg='white',
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.primary_color,
            selectforeground='white',
            state='disabled'
        )
        self.summary_text.pack(fill='both', expand=True)

        # Aba de classificação
        self.classification_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.classification_tab, text='Classificação')

        ttk.Label(self.classification_tab, text="Classificação de Sentimento:").pack(anchor='w')

        self.classification_text = scrolledtext.ScrolledText(
            self.classification_tab,
            wrap=tk.WORD,
            font=text_font,
            padx=8,
            pady=8,
            bg='white',
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.primary_color,
            selectforeground='white',
            state='disabled'
        )
        self.classification_text.pack(fill='both', expand=True)

        # Frame de rodapé
        self.footer_frame = ttk.Frame(self.main_frame)
        self.footer_frame.pack(fill='x', pady=(5, 0))

        self.save_button = ttk.Button(
            self.footer_frame,
            text="Salvar",
            command=self.save_to_file,
            style='TButton',
            state='disabled',
            width=10
        )
        self.save_button.pack(side='left', padx=(0, 5))

        self.copy_button = ttk.Button(
            self.footer_frame,
            text="Copiar",
            command=self.copy_to_clipboard,
            style='TButton',
            state='disabled',
            width=15
        )
        self.copy_button.pack(side='left', padx=(0, 5))

        self.clear_button = ttk.Button(
            self.footer_frame,
            text="Limpar",
            command=self.clear_results,
            style='TButton',
            width=10
        )
        self.clear_button.pack(side='left')

        # Barra de progresso verde
        self.progress = ttk.Progressbar(
            self.footer_frame,
            orient='horizontal',
            mode='determinate',
            length=150,
            style="green.Horizontal.TProgressbar"
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

        # Carregar modelo spaCy
        try:
            self.nlp = spacy.load("pt_core_news_sm")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar modelo spaCy: {str(e)}")
            self.nlp = None

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

            # Habilita edição temporária para inserir conteúdo
            self.result_text.config(state='normal')
            self.keywords_text.config(state='normal')
            self.cluster_text.config(state='normal')
            self.entities_text.config(state='normal')
            self.summary_text.config(state='normal')
            self.classification_text.config(state='normal')

            self.result_text.delete(1.0, tk.END)
            self.keywords_text.delete(1.0, tk.END)
            self.cluster_text.delete(1.0, tk.END)
            self.entities_text.delete(1.0, tk.END)
            self.summary_text.delete(1.0, tk.END)
            self.classification_text.delete(1.0, tk.END)

            # Insere cabeçalho formatado
            self.result_text.insert(tk.END, f"TRADUÇÃO: {translation.upper()}\n", 'header')
            self.result_text.insert(tk.END, f"LIVRO: {book.upper()}\n", 'header')
            self.result_text.insert(tk.END, f"CAPÍTULO: {chapter}\n\n", 'header')

            # Insere versículos formatados
            verses_text = []
            full_text = ""
            for verse in text_content:
                self.result_text.insert(tk.END, f"{verse['number']} ", 'verse_number')
                self.result_text.insert(tk.END, f"{verse['text']}\n\n", 'verse')
                verses_text.append(verse['text'])
                full_text += f" {verse['text']}"

            # Desabilita edição novamente
            self.result_text.config(state='disabled')

            # Processa as palavras-chave
            keywords = self.extract_keywords(full_text)
            self.keywords_text.insert(tk.END, "Palavras mais frequentes (excluindo conectivos):\n\n", 'header')

            for word, count in keywords.most_common(50):
                self.keywords_text.insert(tk.END, f"{word}: {count}\n")

            self.keywords_text.config(state='disabled')

            # Processa a clusterização
            if len(verses_text) >= 2:
                self.update_status("Realizando análise de tópicos...", "black")
                self.progress['value'] = 80
                self.root.update()

                clusters = self.cluster_verses(verses_text)
                self.show_clusters(clusters, text_content)
            else:
                self.cluster_text.insert(tk.END, "Pelo menos 2 versículos são necessários para análise de tópicos.")

            self.cluster_text.config(state='disabled')

            # Processa entidades e atributos linguísticos
            self.update_status("Analisando entidades e atributos...", "black")
            self.progress['value'] = 85
            self.root.update()
            self.analyze_entities(full_text)

            # Processa sumarização
            self.update_status("Gerando resumos...", "black")
            self.progress['value'] = 90
            self.root.update()
            self.generate_summaries(full_text, len(verses_text))

            # Processa classificação
            self.update_status("Classificando texto...", "black")
            self.progress['value'] = 95
            self.root.update()
            self.classify_text(verses_text)

            self.update_status(f"Texto extraído e analisado com sucesso de {parsed_url.netloc}!", self.success_color)
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
        """Extrai o texto bíblico considerando todos os números como versículos"""
        full_text = soup.get_text('\n', strip=True)

        verses = []
        current_verse = {'number': '1', 'text': ''}

        for line in full_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            verse_match = re.match(r'^(\d+)\s*(.*)$', line)
            if verse_match:
                if current_verse['text']:
                    verses.append(current_verse)
                current_verse = {
                    'number': verse_match.group(1),
                    'text': verse_match.group(2)
                }
            else:
                if current_verse['text']:
                    current_verse['text'] += ' ' + line
                else:
                    current_verse['text'] = line

        if current_verse['text']:
            verses.append(current_verse)

        if not verses:
            verses.append({
                'number': '1',
                'text': full_text
            })

        return verses

    def extract_keywords(self, text):
        """Extrai palavras-chave importantes, excluindo conectivos comuns"""
        stopwords = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas',
            'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na',
            'nos', 'nas', 'por', 'para', 'com', 'como', 'que',
            'e', 'ou', 'se', 'mas', 'porque', 'pois', 'quando',
            'onde', 'como', 'qual', 'quais', 'quem', 'não', 'sim'
        }

        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stopwords]
        return Counter(keywords)

    def cluster_verses(self, verses_text):
        """Agrupa versículos por similaridade usando TF-IDF e K-means"""
        try:
            vectorizer = TfidfVectorizer(
                max_features=500,
                stop_words=['o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'em', 'no', 'na', 'por', 'para', 'com', 'que', 'e', 'se'],
                min_df=1,
                max_df=0.9
            )

            processed_texts = [re.sub(r'\d+', '', text.lower()) for text in verses_text]
            processed_texts = [re.sub(r'[^\w\s]', '', text) for text in processed_texts]

            X = vectorizer.fit_transform(processed_texts)

            n_verses = len(verses_text)
            n_clusters = min(4, max(2, n_verses // 2))

            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                init='k-means++',
                n_init=10,
                max_iter=300
            )

            kmeans.fit(X)

            return kmeans.labels_
        except Exception as e:
            print(f"Erro na clusterização: {str(e)}")
            return np.zeros(len(verses_text))

    def show_clusters(self, clusters, verses_data):
        """Mostra os clusters na interface"""
        unique_clusters = set(clusters)

        self.cluster_text.insert(tk.END, "Agrupamento de versículos por tópicos:\n\n", 'header')

        for cluster_id in sorted(unique_clusters):
            self.cluster_text.insert(tk.END, f"\n=== Tópico {cluster_id + 1} ===\n", 'header')

            cluster_verses = [v for v, c in zip(verses_data, clusters) if c == cluster_id]

            for verse in cluster_verses:
                self.cluster_text.insert(tk.END, f"{verse['number']} ", 'verse_number')
                self.cluster_text.insert(tk.END, f"{verse['text']}\n\n", 'verse')

            self.cluster_text.insert(tk.END, f"Total de versículos neste tópico: {len(cluster_verses)}\n")

    def analyze_entities(self, text):
        """Extrai entidades (PER, ORG, LOC) e atributos linguísticos (NOUN, VERB, ADJ) com análise estatística"""
        if not self.nlp:
            self.entities_text.insert(tk.END, "Erro: Modelo spaCy não carregado.\n")
            self.entities_text.config(state='disabled')
            return

        try:
            doc = self.nlp(text)

            # Extração de entidades
            entities = {'PER': [], 'ORG': [], 'LOC': []}
            for ent in doc.ents:
                if ent.label_ == 'PER':
                    entities['PER'].append(ent.text)
                elif ent.label_ == 'ORG':
                    entities['ORG'].append(ent.text)
                elif ent.label_ == 'LOC':
                    entities['LOC'].append(ent.text)

            # Extração de atributos linguísticos
            pos_tags = {'NOUN': [], 'VERB': [], 'ADJ': []}
            for token in doc:
                if token.pos_ in pos_tags:
                    pos_tags[token.pos_].append(token.text)

            # Contagem de frequências
            ent_counts = {k: Counter(v).most_common(5) for k, v in entities.items()}
            pos_counts = {k: Counter(v).most_common(5) for k, v in pos_tags.items()}
            total_ents = sum(len(v) for v in entities.values())
            total_pos = sum(len(v) for v in pos_tags.values())

            # Exibir resultados
            self.entities_text.insert(tk.END, "Análise de Entidades e Atributos Linguísticos\n\n", 'header')
            self.entities_text.insert(tk.END, "=== Entidades Nomeadas ===\n")
            for ent_type, counts in ent_counts.items():
                self.entities_text.insert(tk.END, f"\n{ent_type}:\n")
                if counts:
                    for entity, count in counts:
                        self.entities_text.insert(tk.END, f"  {entity}: {count}\n")
                else:
                    self.entities_text.insert(tk.END, "  Nenhuma encontrada\n")
                self.entities_text.insert(tk.END, f"Total de {ent_type}: {len(entities[ent_type])}\n")

            self.entities_text.insert(tk.END, f"\nTotal de entidades: {total_ents}\n")
            self.entities_text.insert(tk.END, "\n=== Atributos Linguísticos ===\n")
            for pos_type, counts in pos_counts.items():
                self.entities_text.insert(tk.END, f"\n{pos_type}:\n")
                if counts:
                    for word, count in counts:
                        self.entities_text.insert(tk.END, f"  {word}: {count}\n")
                else:
                    self.entities_text.insert(tk.END, "  Nenhum encontrado\n")
                self.entities_text.insert(tk.END, f"Total de {pos_type}: {len(pos_tags[pos_type])}\n")

            self.entities_text.insert(tk.END, f"\nTotal de atributos: {total_pos}\n")
            self.entities_text.insert(tk.END, "\n=== Importância ===\n")
            self.entities_text.insert(tk.END, "A identificação de entidades (pessoas, organizações, locais) ajuda a entender os personagens e contextos geográficos do texto bíblico, enquanto os atributos linguísticos (substantivos, verbos, adjetivos) revelam a estrutura narrativa e os elementos descritivos, úteis para análises temáticas e estilísticas.\n")
            self.entities_text.config(state='disabled')
        except Exception as e:
            self.entities_text.insert(tk.END, f"Erro ao processar entidades: {str(e)}\n")
            self.entities_text.config(state='disabled')

    def generate_summaries(self, text, num_verses):
        """Gera sumarização extrativa e extração de palavras-chave"""
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("portuguese"))

            # Ajustar número de sentenças com base no tamanho do texto
            num_sentences = max(3, num_verses // 5)

            # Sumarização extrativa com LexRank
            lex_rank = LexRankSummarizer()
            lex_summary = lex_rank(parser.document, num_sentences)
            lex_summary_text = " ".join(str(sentence) for sentence in lex_summary)

            # Sumarização extrativa com LSA
            lsa_summarizer = LsaSummarizer()
            lsa_summary = lsa_summarizer(parser.document, num_sentences)
            lsa_summary_text = " ".join(str(sentence) for sentence in lsa_summary)

            # Extração de palavras-chave
            keywords = self.extract_keywords(text)
            top_keywords = [word for word, count in keywords.most_common(10)]

            # Exibir resultados
            self.summary_text.insert(tk.END, "Sumarização e Extração de Palavras-chave\n\n", 'header')
            self.summary_text.insert(tk.END, "=== Sumarização Extrativa (LexRank) ===\n")
            self.summary_text.insert(tk.END, f"{lex_summary_text}\n\n")
            self.summary_text.insert(tk.END, "=== Sumarização Extrativa (LSA) ===\n")
            self.summary_text.insert(tk.END, f"{lsa_summary_text}\n\n")
            self.summary_text.insert(tk.END, "=== Palavras-chave ===\n")
            self.summary_text.insert(tk.END, ", ".join(top_keywords) + "\n\n")
            self.summary_text.insert(tk.END, "=== Nota sobre Sumarização Abstrativa ===\n")
            self.summary_text.insert(tk.END, "A sumarização abstrativa não foi implementada devido à complexidade de modelos de geração de texto (e.g., T5, BART) e restrições computacionais. Recomenda-se análise manual para resumos abstrativos.\n\n")
            self.summary_text.insert(tk.END, "=== Relevância ===\n")
            self.summary_text.insert(tk.END, "LexRank destaca sentenças com alta centralidade, sendo eficaz para capturar temas principais. LSA foca em conceitos latentes, podendo ser mais abstrato. Palavras-chave identificam termos centrais, facilitando comparação entre capítulos.\n")
            self.summary_text.config(state='disabled')
        except Exception as e:
            self.summary_text.insert(tk.END, f"Erro ao gerar resumos: {str(e)}\n")
            self.summary_text.config(state='disabled')

    def classify_text(self, verses_text):
        """Classifica versículos por sentimento usando aprendizado supervisionado"""
        try:
            # Dados rotulados expandidos
            sample_texts = [
                ("Deus criou os céus e a terra", "positive"),
                ("A terra era sem forma e vazia", "negative"),
                ("Haja luz", "positive"),
                ("O dilúvio destruiu a terra", "negative"),
                ("Ama o teu próximo como a ti mesmo", "positive"),
                ("A cidade estava em caos", "negative"),
                ("E Deus viu que era bom", "positive"),
                ("Os homens se rebelaram contra Deus", "negative"),
                ("Este é o dia que o Senhor fez", "positive"),
                ("Eles estavam em silêncio", "neutral"),
                ("A criação foi concluída", "neutral"),
                ("O povo caminhava pelo deserto", "neutral")
            ]
            texts, labels = zip(*sample_texts)

            # Vetorização
            vectorizer = TfidfVectorizer(
                max_features=500,
                stop_words=['o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'em', 'no', 'na', 'por', 'para', 'com', 'que', 'e', 'se']
            )
            X = vectorizer.fit_transform(texts)
            y = labels

            # Divisão dos dados
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

            # Treinamento do modelo
            classifier = MultinomialNB()
            classifier.fit(X_train, y_train)

            # Avaliação com validação cruzada
            cv_scores = cross_val_score(classifier, X, y, cv=3, scoring='accuracy')
            y_pred = classifier.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

            # Classificação dos versículos
            X_verses = vectorizer.transform(verses_text)
            predictions = classifier.predict(X_verses)

            # Exibir resultados
            self.classification_text.insert(tk.END, "Classificação de Sentimento dos Versículos\n\n", 'header')
            self.classification_text.insert(tk.END, "=== Métricas do Modelo ===\n")
            self.classification_text.insert(tk.END, f"Acurácia: {accuracy:.2f}\n")
            self.classification_text.insert(tk.END, f"Precisão: {precision:.2f}\n")
            self.classification_text.insert(tk.END, f"Recall: {recall:.2f}\n")
            self.classification_text.insert(tk.END, f"F1-Score: {f1:.2f}\n")
            self.classification_text.insert(tk.END, f"Acurácia Média (Validação Cruzada): {cv_scores.mean():.2f} ± {cv_scores.std():.2f}\n\n")
            self.classification_text.insert(tk.END, "=== Classificação dos Versículos ===\n")
            for i, (verse, pred) in enumerate(zip(verses_text, predictions), 1):
                self.classification_text.insert(tk.END, f"Versículo {i}: {verse[:50]}... -> {pred}\n")
            self.classification_text.insert(tk.END, "\n=== Estratégia de Rotulação ===\n")
            self.classification_text.insert(tk.END, "Os dados foram rotulados manualmente com base no contexto emocional (positivo, neutro, negativo). Para um conjunto real, seria necessário um processo de anotação manual ou uso de datasets existentes.\n")
            self.classification_text.insert(tk.END, "\n=== Relevância ===\n")
            self.classification_text.insert(tk.END, "A classificação de sentimento ajuda a identificar o tom emocional do texto bíblico, útil para análises teológicas ou estudos comparativos entre capítulos.\n")
            self.classification_text.config(state='disabled')
        except Exception as e:
            self.classification_text.insert(tk.END, f"Erro ao classificar texto: {str(e)}\n")
            self.classification_text.config(state='disabled')

    def save_to_file(self):
        self.result_text.config(state='normal')
        content = self.result_text.get(1.0, tk.END)
        self.result_text.config(state='disabled')

        if not content.strip():
            self.show_error("Nenhum conteúdo para salvar.")
            return

        try:
            os.makedirs('output', exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            book = "biblia"
            chapter = "texto"

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
        self.result_text.config(state='normal')
        content = self.result_text.get(1.0, tk.END)
        self.result_text.config(state='disabled')

        if not content.strip():
            self.show_error("Nenhum conteúdo para copiar.")
            return

        try:
            pyperclip.copy(content)
            self.update_status("Texto copiado para a área de transferência!", self.success_color)
        except Exception as e:
            self.show_error(f"Erro ao copiar para área de transferência: {str(e)}")

    def clear_results(self):
        self.result_text.config(state='normal')
        self.keywords_text.config(state='normal')
        self.cluster_text.config(state='normal')
        self.entities_text.config(state='normal')
        self.summary_text.config(state='normal')
        self.classification_text.config(state='normal')

        self.result_text.delete(1.0, tk.END)
        self.keywords_text.delete(1.0, tk.END)
        self.cluster_text.delete(1.0, tk.END)
        self.entities_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        self.classification_text.delete(1.0, tk.END)

        self.result_text.config(state='disabled')
        self.keywords_text.config(state='disabled')
        self.cluster_text.config(state='disabled')
        self.entities_text.config(state='disabled')
        self.summary_text.config(state='disabled')
        self.classification_text.config(state='disabled')

        self.update_status("Pronto para começar.", "black")
        self.save_button.config(state='disabled')
        self.copy_button.config(state='disabled')

    def update_status(self, message, color="black"):
        self.status_label.config(text=message, foreground=color)

    def show_error(self, message):
        self.update_status(f"Erro: {message}", self.error_color)
        messagebox.showerror("Erro", message)

    def show_about(self):
        about_text = """BibleScraper v3.4

Uma ferramenta para extração e análise de textos bíblicos.

Recursos:
- Extração de textos de diversas traduções
- Identificação automática de versículos
- Análise de palavras-chave
- Clusterização de versículos por similaridade
- Análise de entidades e atributos linguísticos
- Sumarização extrativa e extração de palavras-chave
- Classificação de sentimento

Desenvolvido com Python, Tkinter, BeautifulSoup, spaCy, sumy, e scikit-learn.

© 2025 Extração de Textos Bíblicos"""
        messagebox.showinfo("Sobre", about_text)

    def open_docs(self):
        docs_url = "https://github.com bleedart/docs"
        try:
            webbrowser.open_new(docs_url)
        except:
            self.show_error("Não foi possível abrir a documentação.")


if __name__ == "__main__":
    root = tk.Tk()

    window_width = 900
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    app = BibleScraperApp(root)
    root.mainloop()