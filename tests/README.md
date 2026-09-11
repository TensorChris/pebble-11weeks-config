# Kalender-Vertragstests

Einzige fachliche Referenz ist `docs/contracts/calendar-weekday-v1.html`, SHA-256
`3765d401a3861c90a4dce1d5f94c5ce27764bf9e140deaa9e8a2a25ae19c2e8e`.
Der Testlauf verifiziert diese Prüfsumme vor dem Kompilieren. Der Statuswortlaut
„Entwurf“ im freigegebenen Artefakt wird dabei nicht nachträglich verändert.

## Ausführung

Python 3 mit Pillow, einer IANA-Zeitzonendatenbank und ein C-Compiler werden benötigt.
Aus dem Repository-Hauptverzeichnis:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

`CC` und `CFLAGS` können den Compiler bzw. Instrumentierung wählen, zum Beispiel
`CFLAGS='--coverage -O0 -g'`. Der Hosttest benötigt kein Pebble SDK.
Alle generierten Assets, ausführbaren Dateien, Persistenzdateien, Zeichenprotokolle
und Framebuffer liegen im ignorierten Verzeichnis `build/contract-tests/`.
`reported-<platform>-<model>.png` zeigt die tatsächlichen Kalender-Zeichenaufrufe
für den gemeldeten Zeitpunkt 11.09.2026, 23:22 Uhr in Europe/Berlin.

## Was tatsächlich ausgeführt wird

Unverändert kompiliert werden `src/calendar*.c`, `src/config.c`, `src/numbers.c`
und `src/letters.c`. Der Test erzeugt die echte Kalenderebene, liefert deren
öffentlichem Zeit-Update einen aktuellen Zeitwert und ruft die von der echten
Ebene registrierte Zeichenfunktion auf. Das Prüforakel berechnet die 77 erwarteten
Datumswerte unabhängig mit Python `datetime` aus der Vertragsregel.

Die echten Ressourcen `resources/images/background.png`, `number_3x5.png`,
`big_number_3x5.png` und `cap_letters.png` werden in Host-Bitmaps umgewandelt.
Das Test-Harness implementiert die verwendeten Pebble-Grafikoperationen mit einem
1-Bit-Framebuffer inklusive Zeilenpadding für aplite/diorite und einem
ARGB8-Framebuffer für basalt. Es zeichnet echte Ziffern-/Buchstaben-Subbitmaps,
Rahmen und den vorhandenen dreieckigen Wochenpfeil. Assertions prüfen:

- alle 77 tatsächlich gezeichneten Tageswerte und Spalten;
- genau einen Heute-Rahmen und den zugehörigen Kopf-Rahmen samt Position;
- Überschriften, Monats- und Jahresbeschriftungen;
- Pixel der gezeichneten kleinen Ziffern/Buchstaben und sichtbare Rahmenpunkte;
- große Uhrziffern und Rasterressource einschließlich Position/Abmessungen;
- Kalenderwochenanzeige 37 für den gemeldeten Tag sowie Ausblenden dieser Anzeige;
- alle bestehenden Konfigurationsflags über echte Getter;
- gespeicherte Wochenbeginn-Einstellung über echte `save_config`/`load_config`
  und einen neuen Hostprozess mit derselben Persistenzdatei;
- unveränderte Eingabewerte `time_t` und `struct tm` nach dem Zeichnen.

## Zeitmodelle mit Primärquellen

Ein Host-libc-`mktime` verhält sich anders als die beiden relevanten
Pebble-Firmwaregenerationen. `host/runtime.c` ersetzt daher ausschließlich im
Test-Build `localtime` und `mktime`. Die IANA-Zeitzonenregeln liefert der Host;
`timegm` dient nur der gregorianischen Normalisierung.

1. **Original:** [Google-Pebble-Firmware, eingefrorener Import](https://github.com/google/pebble/blob/3b927684809fba173ee54029bdb32c6ae21611b5/src/fw/util/time/mktime.c).
   Der Zeitwert entsteht aus normalisierten Feldern minus `tm_gmtoff` und
   minus einer Stunde bei positivem `tm_isdst`. Anschließend wird die
   Eingabestruktur über `gmtime_r` mit UTC-Feldern überschrieben.
2. **Current:** [Core Devices mktime](https://github.com/coredevices/PebbleOS/blob/9b0fbab2340a1be4207431fcd41032156beaf996/src/fw/util/time/mktime.c)
   und [öffentlicher Wrapper](https://github.com/coredevices/PebbleOS/blob/9b0fbab2340a1be4207431fcd41032156beaf996/src/fw/applib/pbl_std/pbl_std.c).
   Bei bekanntem `tm_isdst` wird `tm_gmtoff` abgezogen, danach die
   Eingabestruktur wieder auf lokale Zeit gesetzt.

Das Harness deckt den von `localtime` gelieferten Fall `tm_isdst >= 0` ab.
Die Offset-Suche des aktuellen Wrappers bei `tm_isdst < 0` wird nicht emuliert;
Produktcode darf neue Abhängigkeiten von diesem Fall nicht mit diesem Harness
allein validieren. [Firmwareänderung vom 08.04.2026](https://github.com/coredevices/PebbleOS/commit/9b0fbab2340a1be4207431fcd41032156beaf996).
Die Uhrfirmware des Nutzers ist unbekannt; beide Modelle sind deshalb enthalten.
Der aktuelle Modus reproduziert bei 23:22 CEST die Verschiebung der 11 nach TH.

## Grenzen des Nachweises

Dies ist ein Integrationstest bis zum erzeugten Kalender-Framebuffer, kein
vollständiger Watch-Emulator. `main.c`, AppMessage/AppSync, die Betriebssystem-
Minutenregistrierung und die zusätzlichen Statusanzeige-Ebenen werden nicht
kompiliert. Der Tageswechseltest liefert die nächste reguläre Minute an die
echte Kalenderebene; er beweist nicht allein, dass das Betriebssystem diesen
Callback ausliefert. Der Umschalttest ruft die öffentlichen Kalenderebenen-
Operationen auf, die `main.c` verwendet; der Transport einer Konfiguration vom
Handy wird nicht emuliert. Optionen außerhalb des Kalenders werden hier über
ihre unveränderten Flags geprüft, nicht über die sichtbaren externen Ebenen.

Die Plattformvarianten testen die tatsächlichen BW/COLOR-Codezweige, aber keine
ARM-ABI, SDK-Verlinkung, Gerätespeichergrenzen oder Installierbarkeit der PBW.
Raster- und Uhrzeitprüfung kontrolliert reale Grafikressourcen und deren
Zeichenpositionen; sie ist kein vollständiger Screenshotvergleich aller
Statusanzeigen. Diese Grenzen müssen ergänzende SDK-/Emulator-/Lieferprüfungen
adressieren. KAL-06 wird durch diesen Hosttest allein nicht erfüllt.

Die eingefrorenen Tests dürfen nicht als neue Vertragsreferenz dienen. Exakte
Koordinaten konkretisieren die vorhandene Darstellung aus KAL-05; sie begründen
keine zusätzlichen Produktanforderungen. Insbesondere werden keine neuen
Kalenderwochenregeln an Jahresgrenzen eingeführt.

## Ergänzende CI-Nachweise

`runtime_probe.py` installiert die tatsächlich gebaute PBW ausschließlich in
lokalen Headless-Emulatoren für aplite, basalt und diorite. In einer einzigen
Verbindung setzt es 11.09.2026 23:22 UTC+2 und vergleicht die vollständigen
Header-/Kalenderpixel mit dem unabhängig datumsgeprüften Hostrenderer. Anschließend
setzt es 23:59:59, lässt die echte Firmware über Mitternacht laufen und prüft
00:00. Damit werden auch `main.c`, SDK-Verlinkung und der echte Minuten-Tick geprüft.
Firmwareversion, Firmware-/PBW-Prüfsummen und Screenshots werden als CI-Artefakte
gesichert. Der Emulatorfall verwendet den korrekten festen Offset dieses Tages;
Sommerzeitregeln werden separat in den Hostfällen geprüft.

`verify_bundle.py` prüft ZIP-Integrität, Watchface-Identität, Konfiguration und
nichtleere Binär-/Ressourcenpakete für alle drei Plattformen. `verify_frozen.py`
vergleicht den Vertrag gegen den Freigabecommit und nach Testfreigabe alle
Testdateien gegen das zuerst eingecheckte SHA-256-Manifest. Nachträgliches Ändern
von Datei und Prüfsumme zusammen wird dadurch ebenfalls abgelehnt. Vor dem ersten
Test-Freeze erlaubt `--candidate` ausschließlich den ausdrücklich als Kandidat
gekennzeichneten Testphasenlauf; danach greift immer die historische Referenz.

Die Pipeline prüft Hosttests und echte Emulatoren unabhängig und verlangt am Ende
beide Ergebnisse. Kandidatenläufe können deshalb erwartungsgemäß rot sein.

Der ergänzte Emulatorlauf sendet echte AppMessage-Konfigurationen mit ACK-Prüfung,
startet die App über das AppRunState-Protokoll neu und prüft den gespeicherten
Wochenbeginn ohne erneutes Senden. Jede vorhandene Anzeigeoption wird sichtbar
an/aus geschaltet; Quiet Time wird über die echte System-Toggle-App aktiviert,
Uhrenbatterie und Bluetooth werden über die QEMU-Gerätezustände bereitgestellt.
Ein zusätzlicher Mitternachtslauf prüft den reinen Minutenmodus (Sekunden und
Rahmen aus). Die Handy-Konfigurationswebseite selbst ist nicht verändert und
wird nicht im Browser automatisiert; ab der Nachricht wird der echte App-Weg geprüft.

`reference-images.json` enthält ausschließlich unveränderliche RGBA-Pixelreferenzen
der vorhandenen Bilder aus Ausgangscommit33ffcf9. Die Prüfung hängt somit nicht
allein von den möglicherweise veränderten Produktbildern ab; Metadaten wie PNG-ICC-
Profile definieren keine fachliche Erwartung.

Nach dem ersten Test-Freeze lädt der Workflow den Verifier mit `git show` aus der
historischen Freeze-Revision. Damit kann ein geänderter Kandidaten-Verifier die
Prüfung nicht selbst umgehen. Wie jeder Repository-Workflow setzt dieser Schutz
voraus, dass Änderungen am Workflow selbst im PR geprüft und nicht ungeprüft
übernommen werden; Repository-Administratoren bleiben die Vertrauensgrenze.
