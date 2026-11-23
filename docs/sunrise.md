# Sunrise Simulation (RGB-CCT) — Home Assistant Blueprint

Künstlicher Sonnenaufgang für beliebige **RGB-CCT-Lampen**: von einer
konfigurierbaren Startfarbe (Default tiefes Rot/Orange) über warmes Weiß bis zum
gewünschten End-Weiß, mit steigender Helligkeit. Gedacht für den Winter
(künstliche Aufgangszeit), funktioniert aber ganzjährig.

> Den Abend (Wind-down) macht Adaptive Lighting — dieser Blueprint ist der Morgen.

## Features

- **Startzeit-Modi** (angelehnt an Adaptive Lighting):
  - `fixed` — feste Uhrzeit (z. B. 06:30)
  - `sunrise_offset` — relativ zum echten Sonnenaufgang (Minuten-Offset)
  - `clamped` — Sonnenaufgang + Offset, begrenzt auf `min`/`max`-Uhrzeit
- RGB-Warmphase → CCT-Übergang (Kelvin), Verhältnis konfigurierbar (`rgb_phase`)
- Helligkeitsrampe mit Gamma-Kurve (`progress ** gamma`)
- **Capability-Erkennung** pro Lampe: RGB-fähige Lampen werden per Farbe gefahren,
  reine CCT-Lampen per Kelvin
- Manuell ausgeschaltete Lampen werden übersprungen (andere laufen weiter)
- Optional **Adaptive-Lighting-Profile pausieren** (`adaptive_lighting.set_manual_control`)
- Optional **Reconnect-Button** für BLE-Lampen (z. B. Beurer TL100)
- End-Aktionen: `stay` / `off` (mit Retry) / `reading` (4000 K, 80 %)

## Installation

### HACS (empfohlen, dann gibt es Update-Hinweise)

1. HACS → **Custom repositories**
2. `https://github.com/lenucksi/ha-light-blueprints` eintragen, Kategorie **Blueprint**
3. Unter „Blueprints" installieren

### Manuell

1. Datei `sunrise_simulation.yaml` nach
   `/config/blueprints/automation/sunrise/sunrise_simulation.yaml` kopieren
   (oder: Einstellungen → Automationen & Szenen → Blueprints → **Blueprint importieren** → URL)
2. Automation anlegen: Einstellungen → Automationen → **Automation erstellen** → Blueprint wählen

## Empfohlene Winter-Werte

| Parameter | Wert |
|---|---|
| `start_mode` | `fixed` (künstliche Aufgangszeit) |
| `start_time` | `06:30` |
| `duration_min` | 20 |
| `step_seconds` | 30 |
| `start_color` | `[255, 100, 20]` (tiefes Orange) |
| `rgb_phase` | 0.6 |
| `warm_ct_kelvin` / `end_kelvin` | 2000 → 4500 |
| `start_brightness` / `max_brightness` | 1 % → 60 % |
| `brightness_gamma` | 1.5 |
| `end_action` | `stay` |
| `schedule_days` | `workdays` |
| `pause_adaptive_lighting` | `true` (+ AL-Switches wählen) |

Für den Sommer eignet sich `start_mode: clamped` mit `min_start_time`/`max_start_time`,
damit der künstliche Aufgang nicht vor der echten Sonne startet.

## Wie es funktioniert

- Trigger: `time_pattern` jede Minute; die **Conditions** berechnen den Startzeitpunkt
  je Modus und feuern im 2-Minuten-Toleranzfenster. So sind alle drei Startmodi mit
  einem Trigger abbildbar (`today_at()`, `state_attr('sun.sun','next_rising')`).
- Optionaler Clamp: nur wenn der Basispunkt **heute** liegt (sonst wäre der nächste
  Sonnenaufgang morgen und der Aufgang würde fälschlich auf `max` geklemmt).
- Die Rampe läuft in `duration_min * 60 / step_seconds` Schritten; pro Schritt wird
  für jede aktive Lampe die Farbe je nach Capability gewählt.
- Der Endzustand erzwingt per Kelvin ein Weiß (bei RGB-Lampen wechselt die Lampe so in
  den nativen Weiß-Modus), mit bis zu 3 Versuchen — robust gegen BLE-Aussetzer.

## Lizenz

MIT
