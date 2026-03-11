"""
Studien-Dashboard (Prototyp) - Phase 3
Entwickelt im Rahmen des Moduls DLBDSOOFPP01_D (Objektorientierte Programmierung mit Python)
Dieses Skript implementiert ein Dashboard zur Überwachung des Studienfortschritts
basierend auf dem Model-View-Controller (MVC) Architekturmuster.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

# ==========================================
# 1. ENUMS (Für Typensicherheit)
# ==========================================
class ModulStatus(str, Enum):
    """Definiert die erlaubten Zustände eines Moduls im Dashboard."""
    OFFEN = "⏳ Offen"
    BESTANDEN = "✅ Bestanden"
    ANERKANNT = "☑️ Anerkannt"

class Bewertungsart(str, Enum):
    """Unterscheidet, ob ein Fach benotet wird oder als unbenotete Vorleistung zählt."""
    BENOTET = "Benotet"
    UNBENOTET = "Unbenotet"


# ==========================================
# 2. DOMÄNENSCHICHT (Model)
# ==========================================
@dataclass
class Pruefungsleistung:
    """
    Datencontainer für die Leistung in einem Modul.
    Nutzt @dataclass für die automatische Generierung von Initialisierungsmethoden.
    """
    note: Optional[float] = None
    status: ModulStatus = ModulStatus.OFFEN

class Modul(ABC):
    """
    Abstrakte Basisklasse für alle Fächer des Studiengangs.
    Implementiert grundlegende Properties und zwingt Kindklassen zur Spezifizierung.
    """
    def __init__(self, name: str, semester: str, ects: int, bewertungsart: Bewertungsart, leistung: Optional[Pruefungsleistung] = None):
        self._name = name
        self._semester = semester
        self._ects = ects
        self._bewertungsart = bewertungsart
        self._leistung = leistung if leistung else Pruefungsleistung()

    # Nutzung von Properties für saubere Datenkapselung statt klassischer Getter
    @property
    def name(self) -> str: return self._name

    @property
    def semester(self) -> str: return self._semester

    @property
    def ects(self) -> int: return self._ects

    @property
    def bewertungsart(self) -> Bewertungsart: return self._bewertungsart

    @property
    def leistung(self) -> Pruefungsleistung: return self._leistung

    @abstractmethod
    def get_modul_typ(self) -> str: 
        """Muss von der erbenden Klasse implementiert werden."""
        pass

    def ist_abgeschlossen(self) -> bool:
        """Prüft, ob das Modul erfolgreich absolviert oder anerkannt wurde."""
        return self._leistung.status in [ModulStatus.BESTANDEN, ModulStatus.ANERKANNT]


class Pflichtmodul(Modul):
    """Repräsentiert ein reguläres Pflichtfach im Lehrplan."""
    def __init__(self, name: str, semester: str, ects: int, bewertungsart: Bewertungsart, semester_empfehlung: int, leistung: Optional[Pruefungsleistung] = None):
        super().__init__(name, semester, ects, bewertungsart, leistung)
        self._semester_empfehlung = semester_empfehlung

    def get_modul_typ(self) -> str: return "Pflichtmodul"


class Wahlpflichtmodul(Modul):
    """Repräsentiert ein belegtes Wahlpflichtfach mit einem spezifischen Schwerpunkt."""
    def __init__(self, name: str, semester: str, ects: int, bewertungsart: Bewertungsart, gewaehlter_schwerpunkt: str, leistung: Optional[Pruefungsleistung] = None):
        super().__init__(name, semester, ects, bewertungsart, leistung)
        self._gewaehlter_schwerpunkt = gewaehlter_schwerpunkt

    def get_modul_typ(self) -> str: return "Wahlpflichtmodul"


# ==========================================
# 3. DATENHALTUNG (Data Access)
# ==========================================
class DatenManager:
    """
    Kapselt den Zugriff auf das Dateisystem.
    Lädt und speichert die Modul-Objekte im JSON-Format für die Persistenz.
    """
    def __init__(self, dateiname: str = "meine_studien_daten.json"):
        self._dateiname = dateiname
        # Initialer Studienplan (Wird geladen, falls keine lokale JSON existiert)
        self._standard_daten = [
            # --- 1. Semester ---
            ["Betriebssysteme, Rechnernetze & vert. Systeme", "1", 5, "Benotet", 1.3, "✅ Bestanden"],
            ["Einführung in Datenschutz und IT-Sicherheit", "1", 5, "Benotet", 1.7, "✅ Bestanden"],
            ["Einführung in Programmierung mit Python", "1", 5, "Benotet", 1.0, "✅ Bestanden"],
            ["Einf. wissenschaftliches Arbeiten für IT", "1", 5, "Benotet", 1.3, "✅ Bestanden"],
            ["Projekt: Objektor. & funkt. Programmierung mit Python", "1", 5, "Benotet", None, "⏳ Offen"],
            
            # --- 2. Semester ---
            ["Einführung in die Netzwerkforensik", "2", 5, "Benotet", None, "⏳ Offen"],
            ["Statistik, Wahrscheinlichkeit & deskriptiv", "2", 5, "Benotet", None, "⏳ Offen"],
            ["Requirements Engineering", "2", 5, "Unbenotet", None, "☑️ Anerkannt"],
            ["Projekt: Agiles Projektmanagement", "2", 5, "Benotet", None, "⏳ Offen"],
            ["Mathematik Grundlagen 1", "2", 5, "Benotet", None, "⏳ Offen"],

            # --- 3. Semester ---
            ["Grundzüge des Systemtestings", "3", 5, "Benotet", None, "⏳ Offen"],
            ["Theoretische Informatik und math. Logik", "3", 5, "Benotet", None, "⏳ Offen"],
            ["Social Engineering und Insider Threats", "3", 5, "Benotet", None, "⏳ Offen"],
            ["Techn. und betriebl. IT-Sicherheitskonzept.", "3", 5, "Benotet", None, "⏳ Offen"],
            ["Projekt: Social Engineering", "3", 5, "Benotet", None, "⏳ Offen"],

            # --- 4. Semester ---
            ["DevSecOps und gängige Software-Schwachstellen", "4", 5, "Benotet", None, "⏳ Offen"],
            ["Kryptografische Verfahren", "4", 5, "Benotet", None, "⏳ Offen"],
            ["Host- und Softwareforensik", "4", 5, "Benotet", None, "⏳ Offen"],
            ["Seminar: Aktuelle Themen Computer Science", "4", 5, "Benotet", None, "⏳ Offen"],
            ["Projekt: Einsatz und Konfiguration von SIEM", "4", 5, "Benotet", None, "⏳ Offen"],

            # --- 5. Semester ---
            ["Threat Modelling", "5", 5, "Benotet", None, "⏳ Offen"],
            ["Standards der Informationssicherheit", "5", 5, "Benotet", None, "⏳ Offen"],
            ["Projekt: Threat Modelling", "5", 5, "Benotet", None, "⏳ Offen"],

            # --- 6. Semester ---
            ["Bachelorarbeit", "6", 10, "Benotet", None, "⏳ Offen"],
            ["Projekt: Allg. Programmierung mit C/C++", "6", 5, "Benotet", None, "⏳ Offen"],

            # --- Wahlpflichtbereich (WPF) ---
            ["Grundlagen der Softwaretechnik", "WPF", 5, "Unbenotet", None, "☑️ Anerkannt"],
            ["Sicherheit im Internet of Things", "WPF", 5, "Benotet", None, "⏳ Offen"],
            ["Kollaboratives Arbeiten", "WPF", 5, "Unbenotet", None, "☑️ Anerkannt"],
            ["Interkulturelle und ethische Kompetenzen", "WPF", 5, "Benotet", None, "⏳ Offen"],
            ["Konfliktmanagement und Mediation", "WPF", 5, "Benotet", None, "⏳ Offen"],
            ["Interaktion und Kommunikation in Org.", "WPF", 5, "Benotet", None, "⏳ Offen"],
            ["Business Intelligence", "WPF", 5, "Benotet", None, "⏳ Offen"],
            ["Projekt: KI-Exzellenz mit Prompttechniken", "WPF", 5, "Benotet", None, "⏳ Offen"],
            
            # --- Fehlende Module für 180 ECTS ---
            ["Studium Generale 1", "WPF", 5, "Unbenotet", None, "☑️ Anerkannt"],
            ["Studium Generale 2", "WPF", 5, "Unbenotet", None, "☑️ Anerkannt"]
        ]

    def daten_laden(self) -> List[Modul]:
        """Lädt die Daten aus der JSON-Datei und instanziiert die Modul-Objekte."""
        rohdaten = []
        if os.path.exists(self._dateiname):
            with open(self._dateiname, "r", encoding="utf-8") as f:
                rohdaten = json.load(f)
        else:
            rohdaten = self._standard_daten.copy()

        module = []
        for daten in rohdaten:
            name, sem, ects, bewertungsart_str, note, status_str = daten
            status = ModulStatus(status_str)
            bewertungsart = Bewertungsart(bewertungsart_str)
            leistung = Pruefungsleistung(note=note, status=status)
            
            # Spezialisierung anhand des Semesters
            if sem == "WPF":
                module.append(Wahlpflichtmodul(name, sem, ects, bewertungsart, "Cybersecurity", leistung))
            else:
                module.append(Pflichtmodul(name, sem, ects, bewertungsart, int(sem) if sem.isdigit() else 0, leistung))
        return module

    def daten_speichern(self, module: List[Modul]) -> None:
        """Serialisiert die Modul-Objekte und speichert sie als JSON-Datei ab."""
        rohdaten = []
        for m in module:
            rohdaten.append([
                m.name, m.semester, m.ects, 
                m.bewertungsart.value, m.leistung.note, m.leistung.status.value
            ])
        
        with open(self._dateiname, "w", encoding="utf-8") as f:
            json.dump(rohdaten, f, indent=4, ensure_ascii=False)


# ==========================================
# 4. LOGIKSCHICHT (Controller)
# ==========================================
class StudienController:
    """
    Zentraler Controller der MVC-Architektur.
    Verwaltet den Modulbestand und führt die Berechnungen der KPIs durch.
    """
    def __init__(self):
        self._daten_manager = DatenManager()
        self._module: List[Modul] = self._daten_manager.daten_laden()

    def get_module(self) -> List[Modul]:
        return self._module

    def berechne_kennzahlen(self) -> Tuple[float, int, int, float, int, float]:
        """
        Berechnet den aktuellen Schnitt, ECTS-Fortschritt und Zeit-Prognosen.
        Achtung: Unbenotete Fächer fließen in die ECTS, aber nicht in den Schnitt ein!
        """
        ZIEL_NOTE = 2.0
        gesamt_ects = sum(m.ects for m in self._module)
        erreichte_ects = 0
        summe_notenpunkte = 0.0
        ects_fuer_schnitt = 0
        ects_offen_benotet = 0

        for m in self._module:
            if m.ist_abgeschlossen():
                erreichte_ects += m.ects
                
            # Der Notenschnitt wird nur aus BENOTETEN Leistungen gebildet
            if m.bewertungsart == Bewertungsart.BENOTET:
                if m.leistung.status == ModulStatus.BESTANDEN and m.leistung.note is not None:
                    summe_notenpunkte += (m.leistung.note * m.ects)
                    ects_fuer_schnitt += m.ects
                elif m.leistung.status == ModulStatus.OFFEN:
                    ects_offen_benotet += m.ects

        aktueller_schnitt = summe_notenpunkte / ects_fuer_schnitt if ects_fuer_schnitt > 0 else 0.0
        
        # Pufferberechnung für die noch offenen, benoteten Fächer
        if ects_offen_benotet > 0:
            relevante_ects_gesamt = ects_fuer_schnitt + ects_offen_benotet
            max_rest = ((ZIEL_NOTE * relevante_ects_gesamt) - summe_notenpunkte) / ects_offen_benotet
            max_rest = round(max_rest, 2)
        else:
            max_rest = "Ziel erreicht!"

        # Zeitliche Prognose (Ausgehend vom festen Studienstart: 1. März 2026)
        heute = datetime.now()
        start_datum = datetime(2026, 3, 1) 
        ziel_monate_gesamt = 24
        
        monate_vergangen = 0 if heute < start_datum else (heute.year - start_datum.year) * 12 + (heute.month - start_datum.month)
        monate_verbleibend = max(0, ziel_monate_gesamt - monate_vergangen)
        ects_pro_monat = round((gesamt_ects - erreichte_ects) / monate_verbleibend, 1) if monate_verbleibend > 0 else 0

        return round(aktueller_schnitt, 2), erreichte_ects, gesamt_ects, max_rest, monate_verbleibend, ects_pro_monat

    def setze_note(self, modul_name: str, note: Optional[float]) -> str:
        """Vergibt eine Note und ändert den Status auf BESTANDEN."""
        for m in self._module:
            if m.name == modul_name:
                if m.ist_abgeschlossen():
                    return "bereits_abgeschlossen"
                
                # Bei unbenoteten Fächern wird keine Zahl gespeichert
                if m.bewertungsart == Bewertungsart.UNBENOTET:
                    m.leistung.note = None
                    m.leistung.status = ModulStatus.BESTANDEN
                else:
                    m.leistung.note = note
                    m.leistung.status = ModulStatus.BESTANDEN
                    
                self._daten_manager.daten_speichern(self._module)
                return "erfolg"
        return "fehler"

    def entferne_note(self, modul_name: str) -> str:
        """Setzt ein Modul zurück in den Status OFFEN und löscht die Note."""
        for m in self._module:
            if m.name == modul_name:
                if m.leistung.status == ModulStatus.OFFEN:
                    return "offen"
                
                m.leistung.note = None
                m.leistung.status = ModulStatus.OFFEN
                self._daten_manager.daten_speichern(self._module)
                return "erfolg"
        return "fehler"


# ==========================================
# 5. PRÄSENTATIONSSCHICHT (View / GUI)
# ==========================================
class DashboardGUI:
    """
    Klasse für die grafische Benutzeroberfläche (Tkinter).
    Empfängt Benutzereingaben und delegiert die Logik an den Controller.
    """
    def __init__(self, root: tk.Tk):
        self._root = root
        self._root.title("Studien-Dashboard (Pythonic MVC Edition)")
        self._root.geometry("1100x650") 
        self._root.configure(bg="#f0f0f0")
        
        self._controller = StudienController()
        
        self._baue_ui()
        self.ui_kennzahlen_updaten()
        self.tabelle_aktualisieren()

    def _baue_ui(self) -> None:
        """Erzeugt das vollständige Layout der Anwendung."""
        # --- KPI Bereich (Kacheln) ---
        frame_kpi = tk.Frame(self._root, bg="#f0f0f0")
        frame_kpi.pack(pady=20, fill="x")

        box1 = tk.Frame(frame_kpi, bg="white", relief="ridge", borderwidth=2)
        box1.pack(side="left", expand=True, fill="both", padx=10)
        tk.Label(box1, text="Aktueller Schnitt", bg="white", font=("Arial", 10)).pack(pady=5)
        self._lbl_schnitt = tk.Label(box1, text="0.0", bg="white", font=("Arial", 20, "bold"), fg="green")
        self._lbl_schnitt.pack()

        box2 = tk.Frame(frame_kpi, bg="white", relief="ridge", borderwidth=2)
        box2.pack(side="left", expand=True, fill="both", padx=10)
        tk.Label(box2, text="Fortschritt ECTS", bg="white", font=("Arial", 10)).pack(pady=5)
        self._lbl_ects = tk.Label(box2, text="0 / 180", bg="white", font=("Arial", 20, "bold"))
        self._lbl_ects.pack()

        box3 = tk.Frame(frame_kpi, bg="white", relief="ridge", borderwidth=2)
        box3.pack(side="left", expand=True, fill="both", padx=10)
        tk.Label(box3, text="Max. erlaubter Ø Rest", bg="white", font=("Arial", 10)).pack(pady=5)
        self._lbl_puffer = tk.Label(box3, text="0.0", bg="white", font=("Arial", 20, "bold"), fg="blue")
        self._lbl_puffer.pack()

        box4 = tk.Frame(frame_kpi, bg="white", relief="ridge", borderwidth=2)
        box4.pack(side="left", expand=True, fill="both", padx=10)
        tk.Label(box4, text="Zeit-Budget (ab März 2026)", bg="white", font=("Arial", 10)).pack(pady=5)
        self._lbl_zeit = tk.Label(box4, text="Noch 0 Mon.", bg="white", font=("Arial", 20, "bold"), fg="#ff8c00")
        self._lbl_zeit.pack()
        self._lbl_zeit_info = tk.Label(box4, text="Nötig: 0 ECTS/Monat", bg="white", font=("Arial", 10), fg="gray")
        self._lbl_zeit_info.pack(pady=(0, 5))

        # --- Filter Bereich ---
        frame_filter = tk.Frame(self._root, bg="#f0f0f0")
        frame_filter.pack(pady=10)

        tk.Button(frame_filter, text="Alle anzeigen", width=12, command=self._cmd_filter_alle).pack(side="left", padx=5)
        tk.Button(frame_filter, text="Nur Offene", width=12, command=self._cmd_filter_offene).pack(side="left", padx=5)
        tk.Button(frame_filter, text="Nur Bestandene", width=14, command=self._cmd_filter_bestandene).pack(side="left", padx=5)
        tk.Button(frame_filter, text="Nur Anerkannte", width=14, command=self._cmd_filter_anerkannte).pack(side="left", padx=5)
        
        ttk.Separator(frame_filter, orient='vertical').pack(side="left", fill='y', padx=15)
        
        tk.Label(frame_filter, text="Semester auswählen:", bg="#f0f0f0").pack(side="left", padx=(0, 5))
        self._combo_sem = ttk.Combobox(frame_filter, values=["Alle", "1", "2", "3", "4", "5", "6", "WPF"], width=5)
        self._combo_sem.set("Alle")
        self._combo_sem.pack(side="left")
        tk.Button(frame_filter, text="Filtern", command=self._cmd_filter_sem, bg="#e6e6e6").pack(side="left", padx=5)

        # --- Tabellen Bereich ---
        frame_tabelle = tk.Frame(self._root)
        frame_tabelle.pack(pady=10, fill="both", expand=True, padx=20)

        scrollbar = ttk.Scrollbar(frame_tabelle, orient="vertical")
        
        spalten = ("modul", "semester", "ects", "note", "status")
        self._tabelle = ttk.Treeview(frame_tabelle, columns=spalten, show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self._tabelle.yview)

        for col, text in zip(spalten, ["Modulname", "Semester", "ECTS", "Note", "Status"]):
            self._tabelle.heading(col, text=text)

        self._tabelle.column("modul", width=350)
        self._tabelle.column("semester", width=80, anchor="center")
        self._tabelle.column("ects", width=50, anchor="center")
        self._tabelle.column("note", width=50, anchor="center")
        self._tabelle.column("status", width=120)
        
        scrollbar.pack(side="right", fill="y")
        self._tabelle.pack(side="left", fill="both", expand=True)

        # --- Eingabe Bereich ---
        frame_eingabe = tk.Frame(self._root, bg="#e0e0e0", relief="groove", borderwidth=2)
        frame_eingabe.pack(pady=10, fill="x", padx=20)
        
        tk.Label(frame_eingabe, text="1. Fach anklicken ➔ 2. Note eingeben:", bg="#e0e0e0").pack(side="left", padx=10, pady=10)
        self._entry_note = tk.Entry(frame_eingabe, width=10)
        self._entry_note.pack(side="left", padx=5)
        
        tk.Button(frame_eingabe, text="Note eintragen", command=self._cmd_note_speichern, bg="lightblue").pack(side="left", padx=5)
        tk.Button(frame_eingabe, text="Status/Note entfernen", command=self._cmd_note_entfernen, bg="#ff9999").pack(side="right", padx=10)

    def ui_kennzahlen_updaten(self) -> None:
        """Aktualisiert die vier KPI-Kacheln im oberen Bereich der GUI."""
        schnitt, erreichte, gesamt, puffer, monate, pace = self._controller.berechne_kennzahlen()
        
        self._lbl_schnitt.config(text=str(schnitt))
        self._lbl_ects.config(text=f"{erreichte} / {gesamt}")
        
        if monate > 0:
            self._lbl_zeit.config(text=f"Noch {monate} Mon.", fg="#ff8c00") 
            self._lbl_zeit_info.config(text=f"Nötig: {pace} ECTS/Monat")
        else:
            self._lbl_zeit.config(text="Zeit abgelaufen!", fg="red") 
            self._lbl_zeit_info.config(text="Bitte Ziel anpassen")
        
        fg_puffer = "red" if isinstance(puffer, float) and puffer < 1.0 else "blue"
        self._lbl_puffer.config(text=str(puffer), fg=fg_puffer)

    def tabelle_aktualisieren(self, filter_status: Optional[ModulStatus] = None, filter_sem: str = "Alle") -> None:
        """Leert die aktuelle Tabelle und füllt sie neu, basierend auf den aktiven Filtern."""
        for row in self._tabelle.get_children():
            self._tabelle.delete(row)
            
        for m in self._controller.get_module():
            status_passt = (filter_status is None) or (m.leistung.status == filter_status)
            sem_passt = (filter_sem == "Alle") or (m.semester == filter_sem)
            
            if status_passt and sem_passt:
                anzeige_note = m.leistung.note if m.leistung.note is not None else "---"
                self._tabelle.insert("", tk.END, values=(m.name, m.semester, m.ects, anzeige_note, m.leistung.status.value))

    # --- Button-Commands ---
    def _cmd_filter_alle(self) -> None:
        self._combo_sem.set("Alle")
        self.tabelle_aktualisieren(None, "Alle")

    def _cmd_filter_offene(self) -> None:
        self._combo_sem.set("Alle")
        self.tabelle_aktualisieren(ModulStatus.OFFEN, "Alle")

    def _cmd_filter_bestandene(self) -> None:
        self._combo_sem.set("Alle")
        self.tabelle_aktualisieren(ModulStatus.BESTANDEN, "Alle")

    def _cmd_filter_anerkannte(self) -> None:
        self._combo_sem.set("Alle")
        self.tabelle_aktualisieren(ModulStatus.ANERKANNT, "Alle")

    def _cmd_filter_sem(self) -> None:
        self.tabelle_aktualisieren(None, self._combo_sem.get())

    def _cmd_note_speichern(self) -> None:
        """Reagiert auf den Speicher-Button, validiert die Eingabe und ruft den Controller auf."""
        ausgewaehlt = self._tabelle.selection()
        if not ausgewaehlt:
            messagebox.showwarning("Fehler", "Bitte wähle ein Fach aus!")
            return

        modul_name = self._tabelle.item(ausgewaehlt)["values"][0]
        eingabe = self._entry_note.get()
        
        note = None
        if eingabe.strip():
            try:
                note = float(eingabe)
                if note < 1.0 or note > 5.0: raise ValueError
            except ValueError:
                messagebox.showerror("Fehler", "Bitte eine Note (z.B. 1.7) eingeben.")
                return
        else:
            for m in self._controller.get_module():
                if m.name == modul_name and m.bewertungsart == Bewertungsart.BENOTET:
                    messagebox.showerror("Fehler", "Für dieses Fach muss eine Note eingegeben werden!")
                    return

        ergebnis = self._controller.setze_note(modul_name, note)
        
        if ergebnis == "bereits_abgeschlossen":
            messagebox.showinfo("Info", "Dieses Fach ist bereits abgeschlossen oder anerkannt!")
        else:
            self._entry_note.delete(0, tk.END)
            self.tabelle_aktualisieren(filter_sem=self._combo_sem.get())
            self.ui_kennzahlen_updaten()

    def _cmd_note_entfernen(self) -> None:
        """Entfernt eine gesetzte Note aus dem ausgewählten Modul."""
        ausgewaehlt = self._tabelle.selection()
        if not ausgewaehlt:
            messagebox.showwarning("Fehler", "Bitte wähle das Fach aus!")
            return

        modul_name = self._tabelle.item(ausgewaehlt)["values"][0]
        ergebnis = self._controller.entferne_note(modul_name)
        
        if ergebnis == "offen":
            messagebox.showinfo("Info", "Das Fach ist bereits offen.")
        elif ergebnis == "erfolg":
            self.tabelle_aktualisieren(filter_sem=self._combo_sem.get())
            self.ui_kennzahlen_updaten()

# ==========================================
# Programmstart
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardGUI(root)
    root.mainloop()