# SPEI Research Notes — Thread 1: SPEI Mechanics

---

## 1. What SPEI is and how it works (foundational)

These sources cover the basic definition, history, and the end-to-end flow of a SPEI transaction. Start here.

###  Primary sources (Banxico)

- **Banxico — SPEI overview page**
  https://www.banxico.org.mx/servicios/sistema-pagos-electronicos-in.html
  *The canonical source. Includes the general-public explanation, the rastreo workflow, and CEP information. Cite this in your README.*

- **Banxico — SPEI Transfers (English)**
  https://www.banxico.org.mx/services/spei_-transfers-banco-mexico.html
  *English version of the SPEI overview, includes the priority queue mechanic ("participants may assign high priority to some payments").*

- **Banxico — Chronology of payment systems**
  https://www.banxico.org.mx/payment-systems/chronology-of-payment-systems.html
  *Historical context: SPEI replaced SPEUA (Extended Use Electronic Payments System) in August 2004. Original fee was MXN $1.00 per transaction (vs SPEUA's avg MXN $2.40).*

### Secondary sources (clean explanations)

- **BBVA México — ¿Qué es SPEI?**
  https://www.bbva.mx/educacion-financiera/creditos/tarjeta-de-credito/que-es-spei.html
  *Clear step-by-step of the transaction flow from user perspective. Good source for typical retail use cases and common error scenarios.*

- **Kueski Blog — ¿Qué es SPEI y cómo funciona?**
  https://www.kueski.com/blog/que-es-spei-y-como-funciona
  *Best concise breakdown of the six-step transaction flow: (1) instruction prepared and digitally signed, (2) instruction sent, (3) Banxico validates format, (4) acknowledgment sent and instruction queued, (5) settlement and notification to both institutions, (6) recipient credits funds.*

- **Cobre — ¿Qué es SPEI y cómo funciona?**
  https://www.cobre.com/blog/que-es-spei-y-como-funciona-en-mexico
  *Modern, business-facing explanation. Quotes "14 million SPEI transactions daily" and frames SPEI as the "rail" that fintechs connect to. Good for understanding the B2B/treasury use case.*

- **Cofers — Qué es SPEI y cómo usarlo correctamente**
  https://cofers.mx/blog/spei-en-mexico-lo-basico-que-debes-conocer/
  *Mentions the technical detail that "SPEI opera bajo códigos cifrados y firmados digitalmente" and that institutions use digital certificates. Useful for the security/cryptography angle.*

- **MITH Talks — SPEI: el sistema que nunca duerme**
  https://mith.mx/blog/spei-el-sistema-que-nunca-duerme-y-por-qu%C3%A9-m%C3%A9xico-es-l%C3%ADder-en-pagos-inmediatos
  *Frames SPEI as a world reference for real-time payments. Notes availability >99.9%. Useful for the "Mexico is a global leader in real-time payments" pitch in your README intro.*

### English-language / academic sources

- **World Bank Group — SPEI Case Study (Fast Payments)**
  https://fastpayments.worldbank.org/sites/default/files/2021-09/World_Bank_FPS_Mexico_SPEI_Case_Study.pdf
  *Best academic-quality overview in English. Covers SPEI's evolution from 11.5 hours/day to 24 hours/day (March 2015), and the regulator-driven origin. Cite this if you want a high-credibility source in your README.*

- **ITU-T workshop paper — Interoperability in the Mexican payments market**
  https://www.itu.int/en/ITU-T/Workshops-and-Seminars/ifds/Documents/S3_3.%20Interoperability%20of%20Mexican%20payment%20systems_Castellanos.pdf
  *Good detail on participant types and history of non-bank participation (allowed since August 2006).*

- **Lightspark — Mexico Real Time Payments (2026)**
  https://www.lightspark.com/knowledge/mexico-real-time-payments
  *Frames SPEI in the context of global real-time payment systems. Notes that SPEI was an early pioneer but Mexico now lags some regional leaders in adoption growth.*

- **Opendue — What is SPEI**
  https://www.opendue.com/glossary/spei-mexico
  *Strong English-language summary. Notes 2024 stats: 5.34 billion transactions, MXN $219 trillion (6.51x GDP). Mentions ISO 20022 trend (not confirmed for SPEI specifically).*

### What to extract for your notes

- One-paragraph definition of SPEI in your own words
- The 6-step transaction flow (use Kueski's framing as a base)
- Historical milestones: launched Aug 13, 2004; replaced SPEUA; extended to 24/7 in 2015; CoDi added 2019; DiMo added 2023
- Settlement model: **Real-Time Gross Settlement (RTGS)** — transactions settled individually, not batched

---

## 2. SPEI vs CoDi vs DiMo (the broader Banxico payments stack)

You need to know SPEI is the rail, and CoDi/DiMo ride on top. Interviewers will ask about this.

- **Expansión — SPEI, CoDi y DiMo: las diferencias**
  https://expansion.mx/economia/2023/08/08/spei-codi-dimo-diferencias-banxico
  *Best concise comparison. Key fact: CoDi uses SPEI infrastructure; CoDi max per transaction is MXN $8,000. DiMo uses phone numbers instead of CLABE.*

- **El Financiero — SPEI, DiMo y CoDi: diferencias**
  https://www.elfinanciero.com.mx/mis-finanzas/2023/08/13/spei-codi-y-dimo-banxico-diferencias-en-herramientas-de-transferencias-elecronicas/
  *Quotes Banxico's framing: SPEI as "una tubería central a la que se conectan los participantes" — the central pipe. Strong analogy for your README.*

- **Nu México Blog — SPEI, CoDi y DiMo**
  https://blog.nu.com.mx/finanzas-personales/diccionario-financiero/spei-codi-y-dimo-diferencias-entre-pagos-digitales/
  *Fintech perspective on the three rails. Notes 82% of population still uses cash as primary payment method (2022 Banxico study). Good context for understanding adoption barriers.*

- **Dinero en Imagen — SPEI, CoDi y Dimo**
  https://www.dineroenimagen.com/tu-dinero/spei-codi-y-dimo-que-son-en-que-se-diferencian-y-cual-te-conviene-usar/184397
  *Frames the three as "complementary but distinct" — useful framing for your domain section.*

- **Puntored — SPEI 2.0 roadmap**
  https://puntored.mx/en/pagos-spei-codi-dimo-mexico-empresas/
  *Mentions "SPEI 2.0" roadmap: massive processing, multi-currency support, intelligent functions. Also touches on Banxico's CBDC ("digital peso") work. Forward-looking context for your README.*

### What to extract for your notes

- 3-sentence comparison: SPEI = the rail, CoDi = QR/NFC layer on SPEI, DiMo = phone-number-as-identifier layer on SPEI
- Key constraint: CoDi capped at MXN $8,000 per transaction
- All three operate 24/7 on the SPEI infrastructure

---

## 3. CLABE structure (essential for your synthetic data generator)

This is the most technically important section. Your synthetic generator will produce CLABE numbers, so you need to understand the bit structure exactly. Without this, your fake data won't pass even a basic sanity check.

### ★ Primary source

- **ABM (Asociación de Bancos de México) — ¿Qué es la CLABE?**
  https://www.abm.org.mx/preguntas-frecuentes/
  *The authoritative source. CLABE = 18 digits split into: 3-digit bank code + 3-digit plaza/branch code + 11-digit account number + 1 check digit. ABM assigns the bank codes.*

### Detailed structure references

- **Wikipedia — CLABE**
  https://en.wikipedia.org/wiki/CLABE
  *Surprisingly thorough. Has the full check digit algorithm and a list of bank codes. **Use this to write your CLABE validator in Python.** Required reading for the generator.*

- **Verificamex — Validador de CLABE Bancaria**
  https://herramientas.verificamex.com/
  *Has an online validator you can test your generator against. Confirms the structure: positions 1-3 (bank), 4-6 (plaza), 7-17 (account), 18 (check digit).*

- **Amafore — CLABE**
  https://amafore.org/aforepedia/clave-bancaria-estandarizada-clabe/
  *Same 18-digit breakdown, official-adjacent source (Mexican pension fund association).*

- **BBVA — Diferencias entre número de cuenta y CLABE**
  https://www.bbva.mx/educacion-financiera/banca-digital/cuenta-digital-numero-de-cuenta-clabe-interbancaria.html
  *Good for understanding that the 11-digit account number portion is the bank's internal account identifier, embedded into the CLABE.*

- **Facturama Blog — CLABE**
  https://facturama.mx/blog/que-significa/clabe-clave-bancaria-estandarizada/
  *Confirms CLABE has been mandatory for interbank transfers since June 1, 2004.*

- **Novacard — CLABE Interbancaria**
  https://novacard.mx/blog/que-es-clabe-interbancaria
  *Good for understanding that the same CLABE format is used by traditional banks AND fintech IFPEs.*

### What to extract for your notes

- The 4-segment structure: `BBB-PPP-AAAAAAAAAAA-C` (3 + 3 + 11 + 1)
- The check digit algorithm (write this as a Python function — this is the first piece of code in your generator)
- A list of major bank codes you'll use in the generator (BBVA 012, Banamex 002, Santander 014, Banorte 072, HSBC 021, Scotiabank 044, Nu 638, etc. — verify these from Banxico's official list)

---

## 4. SPEI volume, statistics, and aggregate distributions

This is what calibrates your synthetic generator to reality. Your fake data should match the shape of real SPEI traffic.

### ★ Primary sources (Banxico)

- **Banxico — Informe Anual sobre las Infraestructuras de los Mercados (PDF)**
  https://www.banxico.org.mx/publicaciones-y-prensa/informe-anual-sobre-las-infraestructuras-de-los-me/%7BE0085475-B1D7-DED0-60AF-05ED88153BDC%7D.pdf
  *The single most important document for your project. Contains transaction volumes, value distributions, participant counts, and historical percentiles. Notes that early SPEI was mainly high-value (P10 = MXN $4,428, P50 = MXN $136K, P90 = MXN $2.3M) but has shifted toward retail.*

- **Banxico — Información operativa del SPEI (PDF)**
  https://www.banxico.org.mx/spei/d/%7B280E813D-23AC-1EB6-5447-FA1786A129CB%7D.pdf
  *Confirms 86 participants, 24/7 operation, date-change at 18:00, and the rules around restricted-hours operations.*

### Recent volume statistics (2025)

- **Quadratín — Transferencias SPEI crecieron 36.8% en 2025**
  https://mexico.quadratin.com.mx/transferencias-por-spei-crecieron-36-8-durante-2025-registra-banxico/
  *Key 2025 stats from Banxico Gov. Victoria Rodríguez Ceja: **7.3 billion transactions in 2025, +36.8% YoY**. **94% of transactions are ≤1,500 UDIs (≈ MXN $13,200)**. This is the critical distribution insight: most SPEI traffic is small retail, not big corporate.*

- **El Cronista — SPEI mueve 10 veces el PIB de México**
  https://www.cronista.com/mexico/pc-celular/spei-mueve-10-veces-el-pib-de-mexico-proceso-7000-millones-de-transferencias-en-2025-bitso/
  *Bitso/Tukan study. **222 transactions per second average rate.** Bitso processed ~$82B USD in 2025 via Bitso Business. Useful for the fintech-participation angle.*

- **Mobile Money LATAM — Banxico reforma el SPEI**
  https://noticias.mobilemoneylatam.com/banxico-reforma-el-spei/
  *2025: 7.3B transactions ≈ MXN $600 trillion (16.8x GDP). Geographic disparity: Mexico City 50% electronic, Chiapas/Oaxaca 80-90% cash. Banxico projects SPEI volume to surpass card networks by end of 2026.*

- **Contexto Sinaloa — México acelera pagos digitales 2025**
  https://contextosinaloa.com/posts/mexico-pagos-digitales-spei-2025-reto-asia-efectivo
  *Same headline 2025 figures. Useful for the broader inclusion/digitalization narrative.*

- **MobileTime — 2025 SPEI México**
  https://mobiletime.la/noticias/26/02/2026/2025-spei-mexico/
  *Quotes Banxico subgovernor Omar Mejía Castelazo: 12 fintechs are now SPEI direct participants; 18% of SPEI volume originates from non-bank institutions.*

### What to extract for your notes

These are your synthetic-data calibration anchors. Pin these numbers:

| Statistic | Value (2025) | Source |
|---|---|---|
| Total annual transactions | ~7.3 billion | Banxico via Quadratín |
| Total annual value | ~MXN $600 trillion (~16.8x GDP) | Banxico |
| Avg transactions per second | ~222 | Bitso/Tukan |
| % of transactions ≤ MXN $13,200 (1,500 UDIs) | **94%** | Banxico |
| YoY growth 2024→2025 | +36.8% | Banxico |
| Direct participants | 84-86 | Banxico / Opendue |
| Indirect participants (served by 4 direct) | 93 institutions (2024) | Banxico Informe Anual |
| Non-bank originated share | ~18% | Banxico subgov. |

For the generator: 94% of your synthetic transactions should be ≤ MXN $13,200. The rest should be a long-tail extending into the millions, with a few outlier "high-value" transactions per day.

---

## 5. Participants (banks and fintechs)

You'll need a realistic list of sender/receiver institutions for your generator.

- **★ Banxico — Lista de Participantes Indirectos (PDF, updated Nov 3, 2025)**
  https://www.banxico.org.mx/servicios/d/%7B4712726D-B920-4193-684A-4A36A673BF4B%7D.pdf
  *Official list of the 4 direct participants that offer indirect access to other institutions: ASP Integra OPC (a SOFIPO), Banorte, Banregio, and STP (the major IFPE).*

- **★ Banxico — Lista de Instituciones Participantes (live)**
  https://www.banxico.org.mx/cep-scl/listaInstituciones.do
  *The canonical, regularly updated list. Use this to extract bank codes and short names for your generator.*

- **SAT — Instituciones bancarias participantes SPEI**
  https://wwwmat.sat.gob.mx/cs/Satellite?blobcol=urldata&blobkey=id&blobtable=MungoBlobs&blobwhere=1461174998012&ssbinary=true
  *Includes brokerages (casas de bolsa), AFOREs, insurance companies — broader participant categories beyond banks.*

- **Banxico — CoDi avances (lista de participantes obligados)**
  https://www.banxico.org.mx/sistemas-de-pago/codi-avances-banco-mexico.html
  *Lists 31 "participantes obligados" of CoDi: UALÁ, ACTINVER, AFIRME, KAPITAL, AZTECA, BANAMEX, BANCOPPEL, BAJIO, BANJERCITO, BANORTE/IXE, BANREGIO, BABIEN, BANSI, BBASE, BBVA, BMONEX, COMPARTAMOS, CONSUBANCO, DONDE, HSBC, INBURSA, INMOBILIARIO, INTERCAM, INVEX, MIFEL, MULTIVA BANCO, PAGATODO, SABADELL, SANTANDER, SCOTIABANK, VEPORMAS. Effectively a list of the major direct SPEI participants.*

- **Dock — SPEI: un agente de cambio**
  https://dock.tech/es/fluid/blog/financiero/spei/
  *Notes that non-bank participation was opened up to expand the network. Useful for the fintech-inclusion narrative.*

- **Spin by OXXO — SPEI**
  https://spinbyoxxo.com.mx/spei
  *Concrete example of a fintech-as-SPEI-participant from the user-facing side. First daily SPEI from Spin is free; OXXO cash deposit commission MXN $10.34 + IVA.*

### What to extract for your notes

- A list of ~30 institutions with their CLABE bank codes for your generator
- Categorical breakdown: traditional banks (~50), brokerages, IFPEs (fintechs like STP, NVIO/Bitso), SOFIPOs
- The ~18% / 82% split between non-bank-originated and bank-originated transactions (use this as a sampling weight in your generator)

---

## 6. SPEI transaction lifecycle: rastreo, CEP, and what data each transaction generates

Every SPEI transaction produces a "Comprobante Electrónico de Pago" (CEP) — the official Banxico-issued receipt. The CEP fields are what your synthetic transaction records should look like.

### ★ Primary sources (Banxico)

- **Banxico — Comprobante Electrónico de Pago (CEP)**
  https://www.banxico.org.mx/cep/
  *The Banxico-hosted CEP lookup. The fields here are exactly what each SPEI transaction stores.*

- **Banxico — Módulo de Información del SPEI (MI-SPEI)**
  https://www.banxico.org.mx/servicios/modulo-informacion-del-spei_-.html
  *Confirms the two identifiers: (1) **número de referencia** = up to 7 digits chosen by sender, (2) **clave de rastreo** = up to 30 alphanumeric positions assigned by the institution.*

- **Banxico — CEP Consulta por lotes**
  https://www.banxico.org.mx/cep-scl/
  *Useful for understanding the bulk-query CSV format: date, beneficiary CLABE, amount, clave de rastreo, sender CLABE.*

### CEP structure and fields

- **Cobre — ¿Qué es el CEP de una transferencia?**
  https://www.cobre.com/blog/que-es-el-cep-de-spei
  *Best explanation of CEP fields and structure. CEP includes: timestamp, amount, número de referencia (sender-chosen), clave de rastreo (system-assigned), sender and receiver name + RFC + CLABE, sender and receiver bank name + RFC, cryptographic seal. Three-layer crypto: serial number of certificate, original chain (data fingerprint), digital seal (Banxico's signature).*

- **Banamex Banca Empresarial — Comprobante SPEI-SPID**
  https://www.banamex.com/resources/bancanets/bne/esp/contenedor/Comprobante%20SPEI-SPID.htm
  *Useful for understanding the corporate/treasury view of CEP queries.*

- **Kardmatch — Cómo rastrear una transferencia SPEI**
  https://blog.kardmatch.com.mx/rastreo-spei
  *Confirms the 30-day clave de rastreo length, and the 30-minute typical delay before CEP is available.*

### What to extract for your notes

This is your **synthetic data schema**. Each row in your generated dataset should have:

| Field | Type | Example |
|---|---|---|
| `transaction_id` | UUID | (your internal ID) |
| `clave_rastreo` | string, ≤30 alphanumeric | "BBVA20260526123456ABCD" |
| `numero_referencia` | int, ≤7 digits | 1234567 |
| `timestamp` | datetime, UTC | 2026-05-26 14:23:45 |
| `monto` | decimal MXN | 4250.00 |
| `cuenta_ordenante` | 18-digit CLABE | 012345678901234567 |
| `nombre_ordenante` | string | "Juan Pérez Hernández" |
| `rfc_ordenante` | string, 13 chars | PEHJ850101ABC |
| `banco_ordenante` | string | "BBVA México" |
| `cuenta_beneficiario` | 18-digit CLABE | 014987654321098765 |
| `nombre_beneficiario` | string | "María García López" |
| `rfc_beneficiario` | string, 13 chars | GALM920215XYZ |
| `banco_beneficiario` | string | "Santander" |
| `concepto_pago` | string, ≤40 chars | "Pago renta mayo" |
| `is_fraud` | bool (label) | False |
| `fraud_type` | enum (when applicable) | None / ATO / APP / mule / smurfing |

This is the schema you'll generate in Week 2.

---

## 7. SPEI operating hours, limits, and edge cases

Your generator needs to model realistic timing patterns. Most fraud happens off-hours or in unusual time windows, so this is critical.

- **★ Banxico — Información operativa del SPEI (PDF)** (same as section 4)
  https://www.banxico.org.mx/spei/d/%7B280E813D-23AC-1EB6-5447-FA1786A129CB%7D.pdf
  *Key: SPEI itself is 24/7, but in **extended hours (between system open and 6:00 AM) and on non-business banking days, only credit institutions and clearing houses are obligated to process incoming payments via electronic channels.** Date-change happens at 18:00. This creates real time-of-day risk patterns.*

- **Compartamos Banco — Qué es el horario SPEI**
  https://www.compartamos.com.mx/compartamos/blog/emprendamos/spei-horarios-limites-y-tiempos-de-acreditacion
  *Bank-level daily limits range from MXN $8,000 to $250,000 depending on the institution. Banxico does NOT impose a per-transaction max, but banks do.*

- **Tribuna de México — ¿Las transferencias SPEI funcionan después de las 4 pm?**
  https://tribunademexico.com/transferencias-spei-4-pm/
  *Confirms the date-change behavior: SPEI sent on a non-business day (e.g., Dec 25) may be recorded with the next business day's date for bank accounting. Important for time-feature engineering.*

- **Infobae — Mantenimiento SPEI 24 oct 2025**
  https://www.infobae.com/mexico/2025/10/24/en-este-horario-no-podras-hacer-transferencias-interbancarias-hoy-24-de-octubre-spei-estara-en-mantenimiento/
  *Concrete example of scheduled maintenance windows (2 hours, 18:00–20:00). Fraud attempts can spike around outages — worth modeling.*

- **Banorte — Banca Móvil Monto Operaciones (PDF)**
  https://www.banorte.com/cms/doc/Banorte-Movil-Monto-Operaciones.pdf
  *Concrete per-bank limits. Useful sanity check for what your generator's max amounts should look like.*

- **BanCoppel — Horarios y Límites (PDF)**
  https://www.bancoppel.com/pdf/horarios-bpi.pdf
  *Another concrete per-bank limits document.*

- **BanRegio — Banca Electrónica Horarios (PDF)**
  https://portalbanregio.s3.amazonaws.com/assets/naranja/img/HorariosBE.pdf
  *Useful: "Fuera de horario: Sábados, domingos, días festivos. Límite: 24,000 UDIs por operación o máximo acumulado" — concrete UDIs-based limits.*

### What to extract for your notes

- SPEI date-change: 18:00 each day
- Extended hours (00:00–06:00 and non-business days): only credit institutions and clearing houses obligated to process
- Per-bank daily limits: MXN $8,000 to $250,000 (retail), much higher for corporate
- Typical settlement time: <30 seconds in normal conditions
- Maintenance windows: occasional 2-hour windows announced in advance

---

## 8. Open questions to research further

These are gaps you'll want to fill in Week 1 or revisit:

1. **Exact messaging protocol**: One English source says SPEI may use ISO 20022 but Banxico documentation doesn't confirm this publicly. Worth a deeper search before Week 2.
2. **Fee structure today**: Banxico's chronology says MXN $1.00 in 2004; current fees per institution vary widely. Check Banxico's current fee schedule.
3. **Bank code list**: Build a definitive table of (bank code, short name, type) from the Banxico CEP institution list — this is week 2 prep work.
4. **Realistic concept_pago patterns**: What do real SPEI concept fields look like? Useful for adding realism (and for any future NLP-on-fraud-descriptions work). Likely covered in fraud typologies research (Thread 2).

---

## Summary: What to take into Week 2

By end of Week 1, you should be able to:

1. Explain SPEI in 2 minutes cold, including RTGS settlement, the 6-step flow, and where it sits vs CoDi/DiMo
2. Cite 2025 aggregate statistics: ~7.3B transactions, ~MXN $600 trillion, 94% under MXN $13,200
3. Generate a valid CLABE in Python, including the check digit
4. List the schema of a SPEI transaction record (12-15 fields)
5. Name at least 20 SPEI participants with their bank codes

Threads 2 (fraud typologies) and 3 (Banxico aggregate stats deep-dive) are next.