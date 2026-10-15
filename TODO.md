# TODO

## Kritisk granskning · 2026-10-15

Prioriteringen nedan bygger på kodgranskning, befintliga tester och riktade
kontroller i Chromium. En sammanhängande spelrunda med den riktiga PM5:an har
inte verifierats i denna granskning. **P1** påverkar loggens korrekthet eller
hindrar ett rättvist spel; **P2** är tydliga funktions- och användbarhetsfel;
**P3** är mindre men konkreta brister.

### P1 · Fixa först

- [ ] **Sluta logga gamla FTMS-värden som nya.** `bridge.py` uppdaterar en enda
  `last_sample` för både watt och Indoor Bike Data, medan `history.py` återanvänder
  senast kända kadens och hastighet. Separera tidsstämplar för watt, kadens och
  hastighet, låt utgångna värden vara okända och rensa dem vid återanslutning.
  Repro: 60 sekunder med enbart färska 0 W-paket efter 50 rpm/20 km/h gav ett
  fortfarande aktivt pass och 333 m falsk distans. Lägg till regressionstest
  för avbruten FTMS-ström och återanslutning.
- [ ] **Starta inte ett spel innan första tramptaget.** Färsk anslutning vid
  0 W/0 rpm startar nu Orbital och fienderna kan anfalla medan spelaren väntar.
  Vänta på faktisk rörelse, visa tydlig väntestatus och börja spelklockan först
  då. Testa PM5 ansluten med nollvärden följt av första positiva mätningen.
- [ ] **Gör arkadmenyn och spelplanen användbara i smala fönster.** `canvas` är
  alltid 1000×690 men `.stage` får proportionerna 1,3 och 0,9 vid brytpunkterna,
  så grafiken dras ut. Vid 390 px täcker wattpanelen rubriken och tredje
  spelkortet klipps. Bevara spelplanens proportioner, håll HUD och alla spelval
  synliga och kontrollera både vanligt fönster och helskärm i flera storlekar.
- [ ] **Visa ärliga summeringar i dashboarden.** De fyra korten summerar endast
  `/api/sessions` senaste 200 pass men ser ut som totaler. Märk nuvarande
  siffror som ”senaste 200” tills en separat aggregering över hela historiken
  finns. Verifiera med fler än 200 pass. Se totaldashboarden nedan.

### P2 · Spel, mätning och längre pass

- [ ] **Koppla Lumens framfart och poäng till trampning.** I Chill går grottan
  framåt vid 0 W (`85 + ratio*65`) och kristaller kan ge poäng utan aktivitet;
  30 sekunder med 0 W gav 100 poäng i test. Bestäm hur stopp och korta pauser
  ska fungera och säkerställ att progression kräver trampning.
- [ ] **Låt Velodrifts väglogik matcha den ritade asfalten.** `kartOnRoad()`
  klassar vissa asfaltspunkter som gräs och vissa gräspunkter som asfalt.
  Använd samma geometri för ritning och kollisions-/fartregler. Testa ett
  sammanhängande varv med pilar och watt; nuvarande test flyttar bilen direkt
  mellan checkpoints och bevisar inte att banan går att köra normalt.
- [ ] **Rita och rensa Lumens träffpartiklar.** Väggträffar anropar `burst()`
  men `drawExtra()` varken visar eller åldrar partiklarna. En längre Chill-runda
  fyller därför `particles` med osynliga objekt. Testa att antalet återgår till
  noll efter träffanimationen.
- [ ] **Anpassa oändliga Chill-lägens HUD.** Velodrift visar 3/3 varv och full
  progressbar även efter varv 3, medan texten fortsätter med 4/3. Lumen visar
  ett 3 km-mål som stannar på 100 % trots fortsatt flygning. Visa aktuell
  distans/varv och ett meningsfullt nästa delmål i Chill.
- [ ] **Förbättra träningsloggens distans och diagram.** PM5:s ackumulerade
  distans läses men loggen integrerar hastighet, vilket kan ge drift. Använd
  giltiga PM5-deltan när de finns och hastighet som reserv, med regler för
  återställning/avbrott. Markera okända luckor i diagram i stället för att dra
  en obruten linje över dem.
- [ ] **Gör dashboarden lättare under långa pass.** Den hämtar om hela valda
  passets mätserie var femte sekund och bygger om hela passlistan, vilket kan
  ge långsam rendering och tappat tangentbordsfokus. Uppdatera endast det som
  ändrats, behåll fokus/scroll och begränsa antalet punkter i diagrammet utan
  att förlora toppar.
- [ ] **Flytta PM5-adress och enhetsetikett till privat lokal konfiguration.**
  Verklig hårdvaruidentifierare ligger nu som standard i publika `bridge.py`,
  och README ber andra användare redigera källkoden. Använd neutral exempeldata
  i repot och gitignorerad lokal konfiguration eller miljövariabler; dokumentera
  uppgradering utan lokala kodändringar. Bedöm separat om äldre Git-historik
  behöver åtgärdas.
- [ ] **Verifiera en verklig träningsrunda från PM5 till spel och logg.** Testa
  stillastående ansluten monitor, första tramptaget, acceleration, kort stopp,
  anslutningsavbrott, återanslutning och spel i helskärm. Komplettera
  webbläsartesterna med körning som använder verkliga tangenter och normal
  spelmekanik, utan direkt ändring av interna spelvariabler.

### P3 · Tydlighet och tillgänglighet

- [ ] Visa neutral arkadstatistik vid spelval i stället för Orbital-specifik
  specialattack, våg och instruktioner innan ett spel valts.
- [ ] Låt piltangenter ändra ett fokuserat wattfält eller `select` i sidopanelen
  även när spelmenyn är öppen; menygenvägarna ska då inte stjäla tangenterna.
- [ ] Uppdatera `aria-label` för den sekundära HUD-mätaren per spel. Den heter
  nu ”Specialattackens laddning” även när den visar varv eller grottdistans.
- [ ] Hantera PM5:s ogiltiga tidsvärde 65535 i barens tid och återstående tid;
  visa streck i stället för 1092:15.
- [ ] Rätta inaktuell text: dashboardens ”Öppna Orbital” ska leda till
  ”Öppna arkaden”, och README ska beskriva Velodrift som befintligt spel även
  i introduktion och arkitekturdiagram.
- [ ] Bedöm åtkomst till träningshistorik på datorer med flera lokala konton.
  Databasfilen är privat, men HTTP-API:t på localhost saknar autentisering och
  kan läsas av andra lokala användare.

## Menystyrning med tangentbord

- [x] Navigera i spelmenyn med piltangenterna.
- [x] Visa tydligt vilket menyval som är markerat.
- [x] Bekräfta med Enter; gå tillbaka med Escape.
- [x] Använd samma styrning för pausmeny och uppgraderingar mellan vågor.
- [x] Säkerställ att det fungerar i helskärm utan mus och utan att skeppet rör sig bakom menyn.

Genomfört: spelmeny, inställningar, pausmeny, uppgraderingar och helskärm.

## Totaldashboard och träningsöversikt

- [ ] Lägg till vecko-, månads-, års- och livstidstotaler.
- [ ] Visa antal pass, träningstid, distans och kalorier för vald period.
- [ ] Visa diagram över utvecklingen och jämför med föregående period.
- [ ] Lägg till val av period, kalenderår och månad samt tydliga datumgränser i lokal tidszon.
- [ ] Summera hela historiken, inte bara de senaste 200 passen i passlistan.
- [ ] Registrera kalorier från PM5 när de finns; skilj uppmätta/loggade värden från eventuella uppskattningar och hantera äldre pass utan kaloridata.
- [ ] Lägg till lekfulla kalorijämförelser, till exempel ”motsvarar X öl”.
- [ ] Gör jämförelsemåttet valbart och visa antagandet, exempelvis ölens volym och kcal per portion. Lägg gärna till fler jämförelser.
- [ ] Behåll all träningshistorik lokalt utanför repot; lägg inte personliga totalsiffror eller exporter på publik GitHub.

## Arkad

- [x] Gemensam spelväljare med piltangenter och mus.
- [x] Velodrift: kartspel med styrning, checkpoints och maxfart vid mål-watt.
- [x] Lumen: grottflygning med trampstyrd lyftkraft och kristaller.
- [x] Samma webbsida, menyer och statistik i fönster och helskärm.
