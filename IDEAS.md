# Idébank

Levande samling för framtida spel och träningsfunktioner.

## Gemensam spelplattform

- Samma lokala PM5-brygga för alla spel; en Bluetoothanslutning.
- Mål-watt anger spelarens bekväma arbetsnivå, separat från spelsvårigheten.
- Chill, Arcade och Intervall som olika sätt att spela.
- Paus vid anslutningsavbrott eller när fliken lämnas; återuppta medvetet.
- Demo utan cykel för att testa styrning och spelidéer.

## Orbital — Space Invaders (första implementationen)

- Piltangenter styr skeppet. Trampandet styr automatisk eldhastighet.
- Lugn trampning ger grundeld, mål-watt ger maximal eldhastighet.
- Energi laddas av trampandet; mellanslag ger 10 sekunder med två parallella skott per salva, utan ökad eldhastighet.
- Vågor, poäng och uppgraderingar mellan vågorna.
- Chill utan förlust av liv, Arcade med liv, Intervall med återhämtning mellan vågor.

## Kart / cykelspel (användarens idé) — första version: Velodrift

Ett cykelspel eller Mario Kart-inspirerat spel med egen grafik och egna banor.

- Piltangenter styr svängar och placering på banan.
- Trampandet bestämmer hastigheten.
- Spelaren väljer **mål-watt**.
- Vid mål-watt och allt däröver har karten **maxfart**. Det ska inte löna sig
  att pressa över målet för att köra fortare.
- Förslag på kurva: `fart = maxfart × clamp(watt / mål_watt, 0, 1)` med mjuk
  acceleration/inbromsning. Ingen gas behövs på tangentbordet.
- Möjliga varianter: tidslopp, spöke från tidigare lopp, datorstyrda motståndare,
  samla föremål, genvägar och banor med olika miljöer.
- Träningsintensitet och AI-svårighet ställs separat.
- Börja med en enkel bana ovanifrån innan perspektiv och fler banor byggs.

## Asteroids

Rotera och styr med tangentbordet. Trampandet laddar sköld och ammunition.
Välj mellan att skjuta och spara energi.

## Survivor

Flytta mellan fiender med pilarna. Automatvapen får sin eldkraft av trampandet.
Samla uppgraderingar mellan vågorna.

## Grottflygning — första version: Lumen

Trampandet ger lyftkraft, pilarna styr i sidled. Jämn effekt hjälper spelaren
att hålla en stabil höjd mellan hinder.

## Basförsvar

Placera torn och välj uppgraderingar med mus/tangentbord. Cykeln genererar
energin som driver basens försvar. Passar lugna, längre pass.

## Expedition / frirull

Utforska landskap eller rymden i egen takt. Trampandet driver färden; välj
vägar, upptäck platser och samla resurser utan tidspress.

## Dashboard och träningshistorik

- Lokal passlogg med tid, distans, snitt-/maxwatt, kadens och kurvor.
- Datan hör inte hemma i det publika repot: databas under XDG_DATA_HOME.
- Framtid: export/import, personliga mål, veckovy, jämförelse av pass,
  spelresultat kopplade till pass, frivillig Concept2 Logbook-synk.
