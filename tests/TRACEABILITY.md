# Traceability zum freigegebenen Kalendervertrag

Referenz: `docs/contracts/calendar-weekday-v1.html`.
SHA-256: `3765d401a3861c90a4dce1d5f94c5ce27764bf9e140deaa9e8a2a25ae19c2e8e`.
Diese Matrix ist ein Prüfindex, kein zusätzlicher Vertrag.

| Anforderung | Automatisierter Test in `test_calendar.py` | Beobachteter Nachweis |
|---|---|---|
| KAL-01: 11.09.2026 unter Freitag, beide Marker | `test_KAL_01_reported_friday_and_week_37` | Tatsächliche gezeichnete Zahlen und beide Rahmen; 23:22 CEST; beide Firmwaremodelle und alle Plattformzweige |
| KAL-01: Mo–So = 7–13, KW 37 | `test_KAL_01_reported_friday_and_week_37` | Sieben Zellen der aktuellen Zeile und gezeichnete KW-Ziffern |
| KAL-02: 77 lückenlose gregorianische Daten | `test_KAL_02_month_year_and_gregorian_leap_boundaries`, `assert_calendar` | Unabhängiges Datumsorakel gegen jede der 77 realen Zellen |
| KAL-02: erste Zeile gemäß Monat von heute minus sieben Tagen | Alle Aufrufe von `assert_calendar` | Erste Zelle aus der Vertragsregel, danach alle Folgetage |
| KAL-02: Monatslängen/Schaltjahr/Jahreswechsel | `test_KAL_02_month_year_and_gregorian_leap_boundaries` | 28/29/30/31 Tage, 2000/2024 als Schaltjahre, 2100 ohne Schalttag, Dezember/Januar |
| KAL-02: Monats-/Jahresbeschriftung | `assert_calendar` in KAL-01/02/03/04/05 | Tatsächliche Buchstaben und Ziffern an den dargestellten Monats-/Jahreswechseln |
| KAL-03: Montag und Sonntag | KAL-02, `test_KAL_03_switch_and_reload_persisted_week_start`, KAL-04 | Alle Überschriften, 77 Zellen und beide Marker für beide Einstellungen |
| KAL-03: Umschalten und Neustart mit Speicherung | `test_KAL_03_switch_and_reload_persisted_week_start` | Zwei aufeinanderfolgende Renderzyklen, reales Speichern, neuer Hostprozess, reales Laden, komplette Kalenderprüfung |
| KAL-04: gleiches lokales Datum, jede Stunde | `test_KAL_04_all_hours_offsets_and_dst` | 24 Stunden pro Fall; gültige lokale Uhrzeiten; beide Wochenstarts und Firmwaremodelle |
| KAL-04: positive/negative UTC-Abstände und DST | `test_KAL_04_all_hours_offsets_and_dst` | Berlin, New York, Kiritimati, Pago Pago, Kathmandu; Frühlings-/Herbstwechsel |
| KAL-04: Tageswechsel nächste Minute, genau ein Marker | `test_KAL_04_next_minute_after_midnight` | Echte Kalenderebene um 23:59 und 00:00 einschließlich Jahres-/DST-Nähe; vollständige Daten und genau zwei Rahmen insgesamt |
| KAL-05: Raster, Pixelziffern, Kürzel, Uhrzeit | `test_KAL_05_rendering_platforms_clock_and_options`, `assert_calendar` | Originalgrafiken, reale Sprite-Zeichenfunktionen, Framebuffer-Pixel, feste bestehende Positionen; 12-/24-Stundenformat |
| KAL-05: Optionen bleiben erhalten | `test_KAL_05_rendering_platforms_clock_and_options` | Echte Konfigurationsgetter für einzelne Flags und Kombination; KW-Anzeige sichtbar/ausgeblendet |
| KAL-05: verwendeter Zeitwert unverändert | `assert_calendar` | Bytegleiche Eingabestruktur und unveränderter Zeitstempel nach dem Rendern |
| KAL-05: aplite, basalt, diorite | KAL-01 und KAL-05 | Drei getrennte C-Builds mit Plattformmakros und echten BW/COLOR-Kalenderpfaden |
| KAL-06: Lieferung und Freigabegates | Separater SDK-/PBW-/CI-/Review-Lieferprozess | Nicht durch das Host-Harness beansprucht; vor Abschluss separat zu prüfen |

Die fehlende vollständige `main.c`-/OS-/Handy-Integration und die externen
Statusanzeige-Ebenen sind in `README.md` ausdrücklich abgegrenzt. Ein grüner
Hosttest ersetzt diese ergänzenden Nachweise nicht.

## Ergänzende End-to-End- und Lieferzuordnung

| Anforderung | Ergänzender automatisierter Nachweis |
|---|---|
| KAL-01: reale Freitagsspalte | `runtime_probe.py`: echte PBW-Screenshots aller drei Emulatoren um23:22, vollständiger Kalender-/Headerpixelvergleich |
| KAL-04: echter Tageswechsel spätestens nächste Minute | `runtime_probe.py`: Firmware von23:59:59 über00:00 laufen lassen, Bildschirm mit Folgetag vergleichen |
| KAL-05: unterstützte Plattformen und bestehende Darstellung | SDK baut alle drei ARM-Binärdateien; `runtime_probe.py` prüft reale Kalender-/Headerpixel |
| KAL-06: installierbare PBW | `verify_bundle.py` und erfolgreicher Installationsvorgang in `runtime_probe.py` |
| KAL-06: unveränderter Vertrag und Tests | `verify_frozen.py`, historisches Testmanifest und Freigabecommit; CI-Abschlussgate |
| KAL-06: unabhängiges Testreview, gemeinsamer PR | Gesonderter nur lesender Codex-Testreview und PR gegen main; Prozessnachweis im Reviewprotokoll |
