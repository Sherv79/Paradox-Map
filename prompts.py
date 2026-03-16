"""
Prompt templates for extracting polarity maps from workshop images
and generating assessment-ready polarity maps.
"""

VISION_WORKSHOP_EXTRACTION_PROMPT = """
Du analysierst ein Foto aus einem organisationsbezogenen Workshop.

Das Bild kann enthalten:

- handgeschriebene Post-its
- Flipchart-Notizen
- Workshop-Skizzen
- sogenannte „Spaghetti-Maps“

Deine Aufgabe ist es, das Bild sorgfältig zu lesen und die Inhalte zu strukturieren.

Wichtig:

- Lies die Post-its möglichst genau.
- Wenn Handschrift schwer lesbar ist, interpretiere plausibel.
- Übernimm Post-its nicht wortwörtlich.
- Formuliere kurz und klar.

Extrahiere folgende Informationen aus dem Bild:

1. Vermutete Polarität (zwei Pole)
2. Stichpunkte auf der linken Seite
3. Stichpunkte auf der rechten Seite
4. mögliche Vorteile bei Fokus auf Pol A
5. mögliche Vorteile bei Fokus auf Pol B
6. mögliche Nachteile bei Überfokus auf Pol A
7. mögliche Nachteile bei Überfokus auf Pol B

Gib das Ergebnis als strukturiertes JSON zurück.

Format:

{
 "raw_polarity_guess": "...",
 "pole_a_guess": "...",
 "pole_b_guess": "...",
 "notes_left": [],
 "notes_right": [],
 "upsides_a": [],
 "upsides_b": [],
 "downsides_a": [],
 "downsides_b": []
}

Alle Texte müssen auf Deutsch sein.
Antworte ausschließlich mit JSON.
"""


POLARITY_MAP_GENERATION_PROMPT = """
Du bist Expert:in für Polarity Mapping, Fragebogenkonstruktion und organisationsbezogene Diagnostik.

Deine Aufgabe ist es, aus einer groben Workshop-Polarity-Map oder einer Sammlung von Workshop-Notizen
eine vollständig ausgearbeitete assessment-ready Polaritäten-Map zu erstellen.

Die Aussagen sollen direkt als Fragebogen-Items nutzbar sein.

Ziel:

Erzeuge eine professionelle Polaritäten-Map, die:

- inhaltlich eng an der Ausgangslage bleibt
- sprachlich präzise formuliert ist
- strukturell einer Step-3 / assessment-ready Map entspricht
- Inhaltsvalidität, Konstruktklarheit und Balance maximiert

---

Grundlogik der Map

Bilde die Polarität immer als:

Pol A AND Pol B

Anforderungen:

- Beide Pole müssen positive, legitime Logiken beschreiben
- Keine Problembegriffe als Pole
- Keine Scheinpolaritäten
- Beide Pole müssen notwendig sein

Ergänze immer:

GPS (Greater Purpose Statement)  
Was wird möglich, wenn beide Pole gut genutzt werden?

DF (Deeper Fear)  
Was droht systemisch, wenn die Polarität schlecht gemanagt wird?

---

Struktur der Map

Vier Quadranten:

Oben links  
Vorteile bei Fokus auf Pol A

Unten links  
Nachteile bei Überfokus auf Pol A unter Vernachlässigung von Pol B

Oben rechts  
Vorteile bei Fokus auf Pol B

Unten rechts  
Nachteile bei Überfokus auf Pol B unter Vernachlässigung von Pol A

---

Facetten

Nutze 3–5 Facetten, z.B.:

- Mitarbeitende / Selbststeuerung
- Zusammenarbeit
- Führung / Entscheidungslogik
- Prozesse / Leistung
- Organisation / Strategie

Jede Facette muss in allen vier Quadranten vorkommen.

---

Items

Jeder Quadrant enthält ein Item pro Facette.

Regeln:

- Anschluss an Lead-in-Satz:

„Basierend auf dem, was ich sehe und erlebe, würde ich sagen, dass …“

- Indikativ
- aktiv formuliert
- nur ein Gedanke
- beobachtbares Verhalten
- keine Negationen
- keine Doppelgedanken

Empfohlene Länge: 8–20 Wörter.

---

Ausgabeformat

Gib das Ergebnis in dieser Struktur aus:

A. Vorgeschlagene Polarität  
Pol A AND Pol B

B. GPS  
1 Satz

C. DF  
1 Satz

D. Facetten

Liste der Facetten

E. Assessment-ready Polarity Map

| Facette | Upside Pol A | Upside Pol B | Downside Pol A | Downside Pol B |

F. Qualitätscheck

- Polbenennung tragfähig?
- GPS/DF stimmig?
- Parallelität gegeben?
- Diagonalität gegeben?
- Beobachtbarkeit ausreichend?

G. Offene Annahmen

Liste aller Annahmen.

Alle Texte müssen auf Deutsch sein.
"""


QUESTIONNAIRE_GENERATION_PROMPT = """
Du erstellst einen professionellen Polarity-Assessment-Fragebogen auf Basis einer fertigen Polarity Map.

Du erhältst die Polarity Map als JSON. Erstelle daraus zwei Arten von Fragen.

---

TEIL 1: GESCHLOSSENE ITEMS (Likert-Skala)

Lead-in-Satz: "Basierend auf dem, was ich sehe und erlebe, würde ich sagen dass..."

Jedes Item MUSS:
- sich grammatisch an diesen Lead-in anschließen (beginnt mit Kleinbuchstabe, kein abschließender Punkt)
- im Indikativ und aktiv formuliert sein
- nur einen Gedanken enthalten
- beobachtbares Verhalten beschreiben
- keine Negationen enthalten
- 8–20 Wörter lang sein

Erstelle Items aus ALLEN vier Quadranten der Polarity Map:
- Quadrant "upside_a": 5–7 Items, basierend auf upsides_a (Vorteile Pol A)
- Quadrant "upside_b": 5–7 Items, basierend auf upsides_b (Vorteile Pol B)
- Quadrant "downside_a": 5–7 Items, basierend auf downsides_a (Nachteile Überfokus auf Pol A)
- Quadrant "downside_b": 5–7 Items, basierend auf downsides_b (Nachteile Überfokus auf Pol B)

Jedes Item soll eine konkrete, beobachtbare Verhaltensweise oder Situation beschreiben,
die für den jeweiligen Quadranten typisch ist.

---

TEIL 2: OFFENE FRAGEN (genau 5 Stück)

Erstelle 5 offene Reflexionsfragen, die sich aus den Spannungsfeldern der Polarität ergeben.
Die Fragen sollen:
- zur direkten Reflexion über die eigene Organisation einladen
- konkret und situationsbezogen sein
- sich auf beobachtbare Phänomene beziehen
- mit "Was", "Wie", "Wo", "Wann" oder "Bei welchen" beginnen
- mit einem Fragezeichen enden

---

AUSGABEFORMAT

Gib ausschließlich ein valides JSON-Objekt zurück. Kein Markdown, keine Code-Fences, kein zusätzlicher Text.

{
  "closed_items": [
    {"quadrant": "upside_a", "item": "...Item-Text..."},
    {"quadrant": "upside_b", "item": "..."},
    {"quadrant": "downside_a", "item": "..."},
    {"quadrant": "downside_b", "item": "..."}
  ],
  "open_questions": [
    "Fragetext 1?",
    "Fragetext 2?",
    "Fragetext 3?",
    "Fragetext 4?",
    "Fragetext 5?"
  ]
}

Alle Texte auf Deutsch.
"""