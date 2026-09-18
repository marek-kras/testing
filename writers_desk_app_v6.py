import streamlit as st
import sqlite3
from datetime import datetime
import os

# Set page configuration to wide mode for side-by-side panels
st.set_page_config(
    page_title="Writer's Desk",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATABASE SETUP ---
DB_FILE = "writers_desk.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database with tblWork schema from the Writer's Desk design."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tblWork (
            WorkID INTEGER PRIMARY KEY AUTOINCREMENT,
            OriginalTitle TEXT NOT NULL,
            FinalTitle TEXT,
            CreationDate TEXT,
            Language TEXT DEFAULT 'Polish',
            Genre TEXT,
            Status TEXT DEFAULT 'Draft',
            WorkText TEXT,
            Notes TEXT,
            Tags TEXT,
            WorkCode TEXT,
            AuthorID INTEGER DEFAULT 1,
            CreatedAt TEXT,
            UpdatedAt TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tblWork")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sample_works = [
            (
                "Deszcz jesienny", 
                "Cienie we mgle", 
                "2026-09-01", 
                "Polish", 
                "Poetry", 
                "Draft",
                "O szyby deszcz dzwoni, deszcz dzwoni jesienny\nI pluszcze jednaki, miarowy, niezmienny,\nKiedyś o zmierzchu w szarym pokoju\nCzekałem na ciebie w cichym niepokoju...",
                "Inspiracja klasycznym wierszem Staffa. Dopracować rytm w trzeciej strofie.",
                "deszcz, nostalgia, jesień",
                "POE-001",
                1,
                now,
                now
            ),
            (
                "Katedra ze światła", 
                "Katedra", 
                "2026-08-15", 
                "Polish", 
                "Short Story", 
                "Completed",
                "Stali przed wrotami wzniesionymi z czystego, spolaryzowanego światła. \n- Czy to tutaj? - zapytał młodszy inżynier, poprawiając gogle ochronne. \n- Tutaj - odparła, nie odrywając wzroku od mieniących się struktur.",
                "Opowiadanie inspirowane architekturą gotycką i fizyką kwantową.",
                "fantastyka, kosmos, architektura",
                "SHO-002",
                1,
                now,
                now
            )
        ]
        cursor.executemany("""
            INSERT INTO tblWork (
                OriginalTitle, FinalTitle, CreationDate, Language, Genre, Status, 
                WorkText, Notes, Tags, WorkCode, AuthorID, CreatedAt, UpdatedAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_works)
        conn.commit()
    conn.close()

init_db()

# --- LOGIKA KOLEKCJI (COLLECTIONS LOGIC) ---
def init_collections_db():
    """Tworzy tabele dla kolekcji/tomików oraz powiązań z utworami."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tblCollection (
            CollectionID INTEGER PRIMARY KEY AUTOINCREMENT,
            CollectionName TEXT NOT NULL UNIQUE,
            Description TEXT,
            CreatedAt TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tblWorkCollection (
            WorkID INTEGER,
            CollectionID INTEGER,
            PRIMARY KEY (WorkID, CollectionID),
            FOREIGN KEY (WorkID) REFERENCES tblWork(WorkID) ON DELETE CASCADE,
            FOREIGN KEY (CollectionID) REFERENCES tblCollection(CollectionID) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

init_collections_db()

def fetch_all_collections():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tblCollection ORDER BY CollectionName ASC")
    cols = cursor.fetchall()
    conn.close()
    return cols

def insert_collection(name, description=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("INSERT INTO tblCollection (CollectionName, Description, CreatedAt) VALUES (?, ?, ?)",
                       (name.strip(), description.strip(), now))
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        new_id = None
    conn.close()
    return new_id

def update_collection(collection_id, name, description=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE tblCollection SET CollectionName = ?, Description = ? WHERE CollectionID = ?",
            (name.strip(), description.strip(), collection_id)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def delete_collection(collection_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tblWorkCollection WHERE CollectionID = ?", (collection_id,))
    cursor.execute("DELETE FROM tblCollection WHERE CollectionID = ?", (collection_id,))
    conn.commit()
    conn.close()

def fetch_collections_for_work(work_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.* FROM tblCollection c
        JOIN tblWorkCollection wc ON c.CollectionID = wc.CollectionID
        WHERE wc.WorkID = ?
    """, (work_id,))
    cols = cursor.fetchall()
    conn.close()
    return cols

def set_work_collections(work_id, collection_ids):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tblWorkCollection WHERE WorkID = ?", (work_id,))
    for cid in collection_ids:
        cursor.execute("INSERT INTO tblWorkCollection (WorkID, CollectionID) VALUES (?, ?)", (work_id, cid))
    conn.commit()
    conn.close()

# --- LOGIKA AUTORÓW (AUTHORS LOGIC) ---
def init_authors_db():
    """Tworzy tabelę autorów oraz dodaje kolumnę AuthorID do tblWork."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tblAuthor (
            AuthorID INTEGER PRIMARY KEY AUTOINCREMENT,
            AuthorName TEXT NOT NULL UNIQUE,
            IsDefault INTEGER DEFAULT 0
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tblAuthor")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO tblAuthor (AuthorName, IsDefault) VALUES (?, 1)", ("Adam Marek",))
        conn.commit()
    
    try:
        cursor.execute("ALTER TABLE tblWork ADD COLUMN AuthorID INTEGER DEFAULT 1")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

init_authors_db()

def fetch_all_authors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tblAuthor ORDER BY IsDefault DESC, AuthorName ASC")
    authors = cursor.fetchall()
    conn.close()
    return authors

def insert_author(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tblAuthor (AuthorName) VALUES (?)", (name.strip(),))
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        new_id = None
    conn.close()
    return new_id

def get_author_name(author_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT AuthorName FROM tblAuthor WHERE AuthorID = ?", (author_id,))
    row = cursor.fetchone()
    conn.close()
    return row['AuthorName'] if row else "Autor nieznany"

# Lista dostępnych gatunków (Predefined Genre Options)
GENRE_OPTIONS = [
    "Poetry",
    "Short Story",
    "Novel",
    "Essay",
    "Drama",
    "Article",
    "Other"
]

def generate_work_code(genre=""):
    """Generuje automatyczny kod utworu na podstawie gatunku i kolejnego ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(WorkID) FROM tblWork")
    row = cursor.fetchone()
    next_id = (row[0] + 1) if row and row[0] is not None else 1
    conn.close()
    
    prefix = genre[:3].upper() if genre else "WRK"
    return f"{prefix}-{next_id:03d}"

# --- DATABASE CRUD OPERATIONS ---
def fetch_all_works(search_query="", collection_filter="Wszystkie"):
    """Pobiera utwory przefiltrowane po wyszukiwarce oraz wybranej kolekcji."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT DISTINCT w.* FROM tblWork w"
    params = []
    where_clauses = []
    
    if collection_filter == "Bez kolekcji":
        where_clauses.append("w.WorkID NOT IN (SELECT WorkID FROM tblWorkCollection)")
    elif collection_filter != "Wszystkie" and isinstance(collection_filter, int):
        query += " JOIN tblWorkCollection wc ON w.WorkID = wc.WorkID"
        where_clauses.append("wc.CollectionID = ?")
        params.append(collection_filter)
        
    if search_query:
        where_clauses.append("(w.OriginalTitle LIKE ? OR w.FinalTitle LIKE ? OR w.WorkText LIKE ? OR w.Notes LIKE ? OR w.Tags LIKE ?)")
        sq = f"%{search_query}%"
        params.extend([sq, sq, sq, sq, sq])
        
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    query += " ORDER BY w.WorkID DESC"
    
    cursor.execute(query, params)
    works = cursor.fetchall()
    conn.close()
    return works

def fetch_work_by_id(work_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tblWork WHERE WorkID = ?", (work_id,))
    work = cursor.fetchone()
    conn.close()
    return work

def insert_work(original_title, final_title, creation_date, language, genre, status, work_text, notes, tags, work_code, author_id=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO tblWork (
            OriginalTitle, FinalTitle, CreationDate, Language, Genre, Status, 
            WorkText, Notes, Tags, WorkCode, AuthorID, CreatedAt, UpdatedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (original_title, final_title, creation_date, language, genre, status, work_text, notes, tags, work_code, author_id, now, now))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_work(work_id, original_title, final_title, creation_date, language, genre, status, work_text, notes, tags, work_code, author_id=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE tblWork SET 
            OriginalTitle = ?, FinalTitle = ?, CreationDate = ?, Language = ?, 
            Genre = ?, Status = ?, WorkText = ?, Notes = ?, Tags = ?, 
            WorkCode = ?, AuthorID = ?, UpdatedAt = ?
        WHERE WorkID = ?
    """, (original_title, final_title, creation_date, language, genre, status, work_text, notes, tags, work_code, author_id, now, work_id))
    conn.commit()
    conn.close()

def delete_work(work_id):
    """Usuwa utwór z bazy danych SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tblWorkCollection WHERE WorkID = ?", (work_id,))
    cursor.execute("DELETE FROM tblWork WHERE WorkID = ?", (work_id,))
    conn.commit()
    conn.close()

# --- CUSTOM CSS STYLING ---
st.markdown("""
<style>
    /* Styling for the Writer's Desk App */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .writer-header {
        font-family: 'Georgia', serif;
        font-weight: 700;
        color: #2E4057;
        border-bottom: 2px solid #D1D5DB;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .read-panel-title {
        font-family: 'Georgia', serif;
        color: #1F2937;
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .read-panel-subtitle {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        color: #6B7280;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    .read-panel-paper {
        background-color: #FCFBF7;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 30px;
        font-family: 'Georgia', serif;
        font-size: 1.15rem;
        line-height: 1.8;
        color: #2D3748;
        white-space: pre-wrap; /* Keeps line breaks */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        min-height: 400px;
        margin-bottom: 15px;
    }
    .meta-tag {
        background-color: #E0F2FE;
        color: #0369A1;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .sidebar-title {
        font-family: 'Georgia', serif;
        font-weight: bold;
        font-size: 1.3rem;
        color: #1F2937;
        margin-bottom: 15px;
    }
    .print-only-footer {
        display: none;
    }

    /* AUTOMATYCZNE FORMATOWANIE WYDRUKU WARSZTATOWEGO (Ctrl + P) */
    @media print {
        /* 1. Odblokowanie sztywnych ramek Streamlita na czas drukowania */
        html, body, .stApp, [data-testid="stAppViewContainer"], .main, [data-testid="stMain"], .block-container {
            height: auto !important;
            overflow: visible !important;
            position: static !important;
            background: #ffffff !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* 2. Ukrycie nawigacji, nagłówka strony, przycisków, notatek i tagów */
        [data-testid="stSidebar"], 
        [data-testid="stHeader"], 
        header, 
        footer, 
        .stButton, 
        .stAlert, 
        .stCaption, 
        .meta-tag,
        .writer-header,
        .stSubheader {
            display: none !important;
        }

        /* 3. Ukrycie prawego panelu edycji (kolumna 2) */
        [data-testid="column"]:nth-of-type(2), 
        [data-testid="stColumn"]:nth-of-type(2) {
            display: none !important;
        }

        /* 4. Rozciągnięcie podglądu utworu (kolumna 1) na pełne A4 */
        [data-testid="column"]:nth-of-type(1), 
        [data-testid="stColumn"]:nth-of-type(1) {
            width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
            display: block !important;
        }

        /* 5. Czysta kartka papieru (bez obramowań i cieni na wydruku) */
        .read-panel-paper {
            background-color: #ffffff !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            font-size: 1.25rem !important;
            line-height: 2 !important;
            color: #000000 !important;
        }

        /* 6. Dyskretny zapis stopki drukowanej na samym dole */
        .print-only-footer {
            display: block !important;
            margin-top: 60px;
            border-top: 1px solid #94A3B8;
            padding-top: 12px;
            font-size: 0.85rem;
            color: #64748B;
            text-align: center;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE MANAGEMENT ---
if 'selected_work_id' not in st.session_state:
    st.session_state.selected_work_id = None
if 'mode' not in st.session_state:
    st.session_state.mode = 'view' # modes: 'view', 'add'

# Callback to change selected work
def select_work(work_id):
    st.session_state.selected_work_id = work_id
    st.session_state.mode = 'view'

# Callback to switch to "Add New Work" mode
def set_add_mode():
    st.session_state.mode = 'add'
    st.session_state.selected_work_id = None

# --- SIDEBAR: NAVIGATOR & SEARCH ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">✍️ Writer\'s Desk Navigator</div>', unsafe_allow_html=True)
    
    # 1. Wybór i zarządzanie Kolekcjami
    all_collections = fetch_all_collections()
    col_options = {"Wszystkie": "📚 Wszystkie utwory", "Bez kolekcji": "📄 Bez kolekcji"}
    for c in all_collections:
        col_options[c['CollectionID']] = f"📖 {c['CollectionName']}"
        
    selected_col_key = st.selectbox(
        "Filtruj wg kolekcji / tomiku:",
        options=list(col_options.keys()),
        format_func=lambda x: col_options[x]
    )
    
    # Zarządzanie Kolekcjami (Dodawanie / Edycja / Usuwanie)
    with st.expander("⚙️ Zarządzaj kolekcjami (Dodaj / Edytuj / Usuń)"):
        tab_add, tab_edit, tab_del = st.tabs(["➕ Dodaj", "✏️ Edytuj", "🗑️ Usuń"])
        
        with tab_add:
            with st.form(key="quick_add_collection_form"):
                new_col_name = st.text_input("Nazwa nowej kolekcji")
                new_col_desc = st.text_input("Opis (opcjonalnie)")
                add_col_btn = st.form_submit_button("Dodaj kolekcję", use_container_width=True)
                if add_col_btn:
                    if new_col_name.strip():
                        res = insert_collection(new_col_name, new_col_desc)
                        if res:
                            st.success(f"Dodano kolekcję: {new_col_name}")
                            st.rerun()
                        else:
                            st.error("Kolekcja o tej nazwie już istnieje!")
                    else:
                        st.error("Wpisz nazwę kolekcji!")
                        
        with tab_edit:
            if all_collections:
                selected_edit_id = st.selectbox(
                    "Wybierz kolekcję do edycji:",
                    options=[c['CollectionID'] for c in all_collections],
                    format_func=lambda x: next(c['CollectionName'] for c in all_collections if c['CollectionID'] == x),
                    key="select_col_edit"
                )
                col_to_edit = next(c for c in all_collections if c['CollectionID'] == selected_edit_id)
                
                with st.form(key=f"edit_col_form_{selected_edit_id}"):
                    edit_col_name = st.text_input("Nazwa kolekcji", value=col_to_edit['CollectionName'])
                    edit_col_desc = st.text_input("Opis kolekcji", value=col_to_edit['Description'] or "")
                    save_col_btn = st.form_submit_button("Zapisz zmiany w kolekcji", use_container_width=True)
                    if save_col_btn:
                        if edit_col_name.strip():
                            if update_collection(selected_edit_id, edit_col_name, edit_col_desc):
                                st.success("Kolekcja została zaktualizowana!")
                                st.rerun()
                            else:
                                st.error("Kolekcja o tej nazwie już istnieje!")
                        else:
                            st.error("Nazwa kolekcji nie może być pusta!")
            else:
                st.info("Brak utworzonych kolekcji.")

        with tab_del:
            if all_collections:
                col_to_del = st.selectbox(
                    "Wybierz kolekcję do usunięcia:",
                    options=[c['CollectionID'] for c in all_collections],
                    format_func=lambda x: next(c['CollectionName'] for c in all_collections if c['CollectionID'] == x),
                    key="select_col_del"
                )
                if st.button("🗑️ Usuń tę kolekcję", use_container_width=True):
                    delete_collection(col_to_del)
                    st.success("Kolekcja została usunięta!")
                    st.rerun()
            else:
                st.info("Brak utworzonych kolekcji.")

    st.markdown("---")
    
    # 2. Search Box (Equivalent to txtSearch)
    search_query = st.text_input("Wyszukaj utwór... (Search Title / Text / Tag)", value="", placeholder="Tytuł, treść, notatki...")
    
    # "Add New" Button
    st.button("➕ Nowy utwór (Add New)", on_click=set_add_mode, use_container_width=True, type="primary")
    
    st.markdown("---")
    st.markdown("**Lista utworów / Works List**")
    
    # Fetch works based on search query and collection filter
    works_list = fetch_all_works(search_query, selected_col_key)
    
    if works_list:
        for idx, work in enumerate(works_list):
            title = work['OriginalTitle']
            genre = work['Genre'] or "Brak gatunku"
            status = work['Status'] or "Draft"
            work_id = work['WorkID']
            
            # Determine visual indication for the selected work
            is_selected = (st.session_state.selected_work_id == work_id)
            btn_label = f"📖 {title} ({genre})" if is_selected else f"{title} ({genre})"
            
            # Clicking a work selects it
            st.button(
                btn_label, 
                key=f"sidebar_btn_{work_id}_{idx}", 
                on_click=select_work, 
                args=(work_id,), 
                use_container_width=True
            )
    else:
        st.info("Brak utworów pasujących do kryteriów.")

# Set default selection if none and works exist
if st.session_state.selected_work_id is None and st.session_state.mode == 'view' and works_list:
    st.session_state.selected_work_id = works_list[0]['WorkID']

# --- MAIN WORKSPACE ---
st.markdown('<h1 class="writer-header">Writer’s Desk &mdash; Open-Source Edition</h1>', unsafe_allow_html=True)

# ----------------- MODE: VIEW / EDIT (DUAL PANELS) -----------------
if st.session_state.mode == 'view' and st.session_state.selected_work_id is not None:
    work = fetch_work_by_id(st.session_state.selected_work_id)
    
    if work:
        # Create the two columns for side-by-side reading and editing
        col_read, col_edit = st.columns([1, 1], gap="large")
        
        # --- LEFT PANEL: READ PANEL ---
        with col_read:
            st.subheader("📖 Read Panel (Podgląd utworu)")
            
            author_name = get_author_name(work['AuthorID'] if 'AuthorID' in work.keys() and work['AuthorID'] else 1)
            title_disp = work['FinalTitle'] if work['FinalTitle'] else work['OriginalTitle']
            creation_str = f"Powstał: {work['CreationDate']}" if work['CreationDate'] else "Brak daty powstania"
            
            st.markdown(f'<div class="read-panel-title">{title_disp}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="read-panel-subtitle">Autor: <strong>{author_name}</strong> | {work["Genre"]} | {creation_str} | Status: **{work["Status"]}**</div>', unsafe_allow_html=True)
            
            # Display formatted poetry or text
            text_disp = work['WorkText'] if work['WorkText'] else "*Utwór nie zawiera jeszcze tekstu.*"
            st.markdown(f'<div class="read-panel-paper">{text_disp}</div>', unsafe_allow_html=True)
            
            # Hidden print footer (only visible on Ctrl+P)
            today_str = datetime.now().strftime("%Y-%m-%d")
            st.markdown(f'<div class="print-only-footer">Wygenerowano w Writer\'s Desk &bull; Autor: {author_name} &bull; Kod utworu: <strong>{work["WorkCode"]}</strong> &bull; Data: {today_str}</div>', unsafe_allow_html=True)

            # Display Collections
            work_cols = fetch_collections_for_work(work['WorkID'])
            if work_cols:
                st.markdown("**Kolekcje / Tomiki:**")
                for c in work_cols:
                    st.markdown(f'<span class="meta-tag" style="background-color: #FEF3C7; color: #92400E;">📖 {c["CollectionName"]}</span>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

            # Display Tags and Notes
            if work['Tags']:
                st.markdown("**Tagi:**")
                tags_list = [t.strip() for t in work['Tags'].split(',') if t.strip()]
                for tag in tags_list:
                    st.markdown(f'<span class="meta-tag">#{tag}</span>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
            if work['Notes']:
                st.info(f"**Notatki autora:**\n\n{work['Notes']}")
                
            st.caption(f"ID: {work['WorkID']} | Kod: {work['WorkCode']} | Utworzono: {work['CreatedAt']} | Zmodyfikowano: {work['UpdatedAt']}")

        # --- RIGHT PANEL: EDIT PANEL ---
        with col_edit:
            st.subheader("✏️ Edit Panel (Edycja utworu)")
            
            # Use a form to capture all updates
            with st.form(key=f"edit_form_{work['WorkID']}"):
                edit_orig_title = st.text_input("Tytuł roboczy (Original Title) *", value=work['OriginalTitle'])
                edit_final_title = st.text_input("Tytuł ostateczny (Final Title)", value=work['FinalTitle'] or "")
                
                # Wybór / Dopisywanie Autora
                all_authors = fetch_all_authors()
                current_author_id = work['AuthorID'] if 'AuthorID' in work.keys() and work['AuthorID'] else 1
                author_ids = [a['AuthorID'] for a in all_authors]
                current_auth_idx = author_ids.index(current_author_id) if current_author_id in author_ids else 0
                
                c_auth1, c_auth2 = st.columns(2)
                with c_auth1:
                    edit_author_id = st.selectbox(
                        "Autor (Author)", 
                        options=author_ids, 
                        index=current_auth_idx,
                        format_func=lambda x: next(a['AuthorName'] for a in all_authors if a['AuthorID'] == x)
                    )
                with c_auth2:
                    new_author_name = st.text_input("➕ Dodaj nowego autora (opcjonalnie)")

                c1, c2, c3 = st.columns(3)
                with c1:
                    current_genre = work['Genre'] if work['Genre'] in GENRE_OPTIONS else GENRE_OPTIONS[0]
                    genre_idx = GENRE_OPTIONS.index(current_genre) if current_genre in GENRE_OPTIONS else 0
                    edit_genre = st.selectbox("Gatunek (Genre)", options=GENRE_OPTIONS, index=genre_idx)
                with c2:
                    default_date = datetime.today()
                    if work['CreationDate']:
                        try:
                            default_date = datetime.strptime(work['CreationDate'], "%Y-%m-%d")
                        except ValueError:
                            pass
                    edit_creation_date = st.date_input("Data powstania (Creation Date)", value=default_date).strftime("%Y-%m-%d")
                with c3:
                    status_options = ["Draft", "In Progress", "Completed", "Submitted", "Published", "Archived"]
                    current_status_idx = status_options.index(work['Status']) if work['Status'] in status_options else 0
                    edit_status = st.selectbox("Status", options=status_options, index=current_status_idx)
                
                c4, c5 = st.columns(2)
                with c4:
                    edit_language = st.text_input("Język oryginału (Language)", value=work['Language'] or "Polish")
                with c5:
                    edit_code = st.text_input("Kod utworu (Work Code)", value=work['WorkCode'] or "")
                
                edit_text = st.text_area("Tekst utworu (Work Text)", value=work['WorkText'] or "", height=250)
                edit_notes = st.text_area("Notatki (Notes)", value=work['Notes'] or "", height=100)
                
                # --- PRZYPISANIE DO KOLEKCJI ---
                all_cols = fetch_all_collections()
                current_work_cols = fetch_collections_for_work(work['WorkID'])
                current_col_ids = [c['CollectionID'] for c in current_work_cols]
                
                selected_col_ids = st.multiselect(
                    "Przypisz do kolekcji / tomików:",
                    options=[c['CollectionID'] for c in all_cols],
                    default=current_col_ids,
                    format_func=lambda x: next((c['CollectionName'] for c in all_cols if c['CollectionID'] == x), str(x))
                )
                
                new_inline_col = st.text_input(
                    "➕ Stwórz nową kolekcję i przypisz od razu (opcjonalnie):", 
                    placeholder="Wpisz nazwę nowej kolekcji..."
                )

                edit_tags = st.text_input("Tagi (rozdzielone przecinkami)", value=work['Tags'] or "")

                st.markdown("<br>", unsafe_allow_html=True)
                
                col_save_btn, col_del_btn = st.columns([1, 1])
                with col_save_btn:
                    submit_button = st.form_submit_button(label="💾 Zapisz zmiany (Save Changes)", use_container_width=True, type="primary")
                with col_del_btn:
                    delete_button = st.form_submit_button(label="🗑️ Usuń utwór (Delete Work)", use_container_width=True)
                
                if submit_button:
                    if not edit_orig_title.strip():
                        st.error("Tytuł roboczy jest wymagany!")
                    else:
                        # 1. Nowa kolekcja
                        if new_inline_col.strip():
                            created_cid = insert_collection(new_inline_col.strip())
                            if created_cid and created_cid not in selected_col_ids:
                                selected_col_ids.append(created_cid)
                            elif created_cid is None:
                                existing_cid = next((c['CollectionID'] for c in all_cols if c['CollectionName'].lower() == new_inline_col.strip().lower()), None)
                                if existing_cid and existing_cid not in selected_col_ids:
                                    selected_col_ids.append(existing_cid)

                        # 2. Nowy autor
                        if new_author_name.strip():
                            created_aid = insert_author(new_author_name.strip())
                            if created_aid:
                                edit_author_id = created_aid

                        set_work_collections(work['WorkID'], selected_col_ids)
                        update_work(
                            work['WorkID'],
                            edit_orig_title.strip(),
                            edit_final_title.strip() if edit_final_title.strip() else None,
                            edit_creation_date,
                            edit_language.strip(),
                            edit_genre.strip(),
                            edit_status,
                            edit_text,
                            edit_notes,
                            edit_tags,
                            edit_code.strip(),
                            edit_author_id
                        )
                        st.success("Zmiany zostały pomyślnie zapisane!")
                        st.rerun()
                
                if delete_button:
                    delete_work(work['WorkID'])
                    st.session_state.selected_work_id = None
                    st.success("Utwór został pomyślnie usunięty!")
                    st.rerun()

# ----------------- MODE: ADD NEW (INJECTION FORM) -----------------
elif st.session_state.mode == 'add':
    st.subheader("➕ Inject New Work to Database (Dodaj nowy utwór)")
    
    with st.form(key="add_new_work_form"):
        new_orig_title = st.text_input("Tytuł roboczy (Original Title) *", placeholder="Np. Jesienne liście")
        new_final_title = st.text_input("Tytuł ostateczny (Final Title)", placeholder="Pozostaw puste, jeśli nie znasz ostatecznego")
        
        # Wybór / Dodawanie Autora dla nowego utworu
        all_authors = fetch_all_authors()
        author_ids = [a['AuthorID'] for a in all_authors]
        
        c_auth1, c_auth2 = st.columns(2)
        with c_auth1:
            new_author_id = st.selectbox(
                "Autor (Author)", 
                options=author_ids, 
                format_func=lambda x: next(a['AuthorName'] for a in all_authors if a['AuthorID'] == x)
            )
        with c_auth2:
            new_author_name_input = st.text_input("➕ Dodaj nowego autora do bazy (opcjonalnie)", key="new_author_input_add")

        c1, c2, c3 = st.columns(3)
        with c1:
            new_genre = st.selectbox("Gatunek (Genre)", options=GENRE_OPTIONS)
        with c2:
            new_creation_date = st.date_input("Data powstania (Creation Date)", value=datetime.today()).strftime("%Y-%m-%d")
        with c3:
            new_status = st.selectbox("Status", options=["Draft", "In Progress", "Completed", "Submitted", "Published", "Archived"])
            
        c4, c5 = st.columns(2)
        with c4:
            new_language = st.text_input("Język oryginału (Language)", value="Polish")
        with c5:
            autogen_code = generate_work_code(new_genre)
            new_code = st.text_input("Kod utworu (Work Code - wygenerowany)", value=autogen_code, disabled=True)
            
        new_text = st.text_area("Tekst utworu (Work Text)", placeholder="Wpisz lub wklej swój tekst tutaj...", height=300)
        new_notes = st.text_area("Notatki (Notes)", placeholder="Notatki o inspiracji, poprawkach, strukturze...", height=100)
        new_tags = st.text_input("Tagi / Słowa kluczowe (rozdzielone przecinkami)", placeholder="Np. wiatr, las, wieczór")
        
        all_cols = fetch_all_collections()
        selected_new_col_ids = []
        if all_cols:
            selected_new_col_ids = st.multiselect(
                "Przypisz do kolekcji / tomików:",
                options=[c['CollectionID'] for c in all_cols],
                format_func=lambda x: next(c['CollectionName'] for c in all_cols if c['CollectionID'] == x)
            )

        st.markdown("<br>", unsafe_allow_html=True)
        col_cancel, col_save = st.columns([1, 1])
        
        with col_cancel:
            cancel_button = st.form_submit_button(label="Anuluj (Cancel)", use_container_width=True)
            if cancel_button:
                st.session_state.mode = 'view'
                st.rerun()
                
        with col_save:
            save_button = st.form_submit_button(label="Zapisz i wyświetl (Save & Load)", use_container_width=True, type="primary")
            if save_button:
                if not new_orig_title.strip():
                    st.error("Tytuł roboczy jest wymagany!")
                else:
                    if new_author_name_input.strip():
                        created_aid = insert_author(new_author_name_input.strip())
                        if created_aid:
                            new_author_id = created_aid

                    new_id = insert_work(
                        new_orig_title.strip(),
                        new_final_title.strip() if new_final_title.strip() else None,
                        new_creation_date,
                        new_language.strip(),
                        new_genre.strip(),
                        new_status,
                        new_text,
                        new_notes,
                        new_tags,
                        new_code.strip(),
                        new_author_id
                    )
                    set_work_collections(new_id, selected_new_col_ids)
                    st.session_state.selected_work_id = new_id
                    st.session_state.mode = 'view'
                    st.success("Dodano nowy utwór!")
                    st.rerun()
