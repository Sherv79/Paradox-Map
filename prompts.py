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