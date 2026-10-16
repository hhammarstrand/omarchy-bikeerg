# TODO

## Kritisk granskning · 2026-10-15

Åtgärdat och testat 2026-10-16 där rutan är kryssad. Tester använder syntetisk
PM5-data och Chromium; en fysisk slutkontroll väntar fortfarande.

### P1 · Datakvalitet och spelstart

- [x] Ge varje PM5-värde egen tidsstämpel och rensa gamla värden vid
  återanslutning. Loggen slutar nu förlänga ett pass och lägga till distans när
  bara 0 W-paket kommer in; regressionstest täcker det tidigare felet som gav
  333 m falsk distans på 60 sekunder.
- [x] Vänta på första positiva wattmätningen innan ett spel och dess klocka
  startar. Orbital kan därmed inte förlora sköldar medan användaren väntar på
  första tramptaget.
- [x] Behåll spelplanens 1000:690-proportioner i smala fönster. Arkadmenyn
  visas utan att wattpanelen täcker rubriken eller tredje spelkortet klipps.
- [x] Låt periodkorten i dashboarden summera hela historiken. Passlistan är
  fortsatt begränsad till 200; ett test med 205 pass verifierar totalerna.

### P2 · Spel, mätning och längre pass

- [x] Knyt Lumens framfart och poäng till watt. Vid 0 W står expeditionens
  distans stilla även i Chill.
- [x] Använd samma bankant för Velodrifts ritning och fartregel. Ett helt varv
  har körts med riktiga piltangenttryck i webbläsartestet, utan teleportering.
- [x] Visa och rensa träffpartiklar även i Velodrift och Lumen; testet väntar
  tills partiklar efter en effekt har försvunnit.
- [x] Ge Chill-lägena återkommande delmål i HUD: nästa varv i Velodrift och
  nästa 500 m i Lumen, utan fastlåst 3/3 eller 3 km-mätare.
- [x] Använd PM5:s ackumulerade distans när den är färsk och hastighet som
  reserv. Diagram markerar mätluckor i stället för att binda ihop dem.
- [x] Begränsa passdiagrammens datapunkter med toppar bevarade. Dashboarden
  hämtar bara om detaljer när passet ändras och behåller listans fokus/scroll.
- [x] Flytta aktuell PM5-adress och enhetsetikett till en privat konfigurationsfil
  utanför repot. Ett neutralt exempel finns i repot. Äldre publika Git-commits
  innehåller fortfarande den tidigare identifieraren; historiken har inte
  skrivits om eftersom det skulle bryta befintliga kloner.
- [ ] Kör en hel fysisk PM5-runda: stillastående ansluten monitor, första
  tramptaget, acceleration, kort stopp, avbrott, återanslutning och helskärm.
  Syntetiska flöden och ett komplett Velodrift-varv är redan testade.

### P3 · Tydlighet och tillgänglighet

- [x] Visa neutral arkadvy innan ett spel väljs, utan Orbital-specifika mätare.
- [x] Låt piltangenter ändra ett fokuserat wattfält eller val i sidopanelen;
  under aktivt spel styr vänster/höger fortfarande även efter demo-reglaget.
- [x] Uppdatera den sekundära HUD-mätarens skärmläsaretikett per spel.
- [x] Visa streck för PM5:s ogiltiga tidsvärde 65535 i baren.
- [x] Rätta dashboardens arkadlänk och README:s inaktuella spelbeskrivningar.
- [x] Bedöm åtkomst på datorer med flera lokala konton. Databasen är 0600 men
  localhost-API:t saknar användarautentisering; detta dokumenteras nu i README.
  En separat autentiseringslösning behövs om datorn delas mellan konton.

## Menystyrning med tangentbord

- [x] Navigera i spelmenyn med piltangenterna.
- [x] Visa tydligt vilket menyval som är markerat.
- [x] Bekräfta med Enter; gå tillbaka med Escape.
- [x] Använd samma styrning för pausmeny och uppgraderingar mellan vågor.
- [x] Säkerställ att det fungerar i helskärm utan mus och utan att skeppet rör sig bakom menyn.

Genomfört: spelmeny, inställningar, pausmeny, uppgraderingar och helskärm.

## Totaldashboard och träningsöversikt

- [x] Lägg till vecko-, månads-, års- och livstidstotaler.
- [x] Visa antal pass, träningstid, distans och kalorier för vald period.
- [x] Visa diagram över utvecklingen och jämför med föregående period.
- [x] Lägg till val av period, kalenderår och månad samt tydliga datumgränser i lokal tidszon.
- [x] Summera hela historiken, inte bara de senaste 200 passen i passlistan.
- [x] Registrera kalorier från PM5 när de finns; skilj uppmätta/loggade värden från eventuella uppskattningar och hantera äldre pass utan kaloridata.
- [x] Lägg till lekfulla kalorijämförelser, till exempel ”motsvarar X öl”.
- [x] Gör jämförelsemåttet valbart och visa antagandet, exempelvis ölens volym och kcal per portion. Lägg gärna till fler jämförelser.
- [x] Behåll all träningshistorik lokalt utanför repot; lägg inte personliga totalsiffror eller exporter på publik GitHub.

## Arkad

- [x] Gemensam spelväljare med piltangenter och mus.
- [x] Velodrift: kartspel med styrning, checkpoints och maxfart vid mål-watt.
- [x] Lumen: grottflygning med trampstyrd lyftkraft och kristaller.
- [x] Samma webbsida, menyer och statistik i fönster och helskärm.
