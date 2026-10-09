# Data audit of the old fixture saves (2026-10-06)

Classifier: `backend/app/trade/quality.py` (R12 final: trade is computed on the 1st; clean = a save from the 1st after the
game's first computation, with none of the player's own merchants or fleets on the way, on the supported game version).
AI traffic on the way is allowed and listed; it is absent from both the trade entries and the computed values.
Envoy `action` 1 = merchant on the way (action-2 envoys equal the country's `has_trader` entries in 1,947 of 1,950 country-saves).
Script: `backend/scripts/data_audit.py`.

**8 of 110 saves are clean.**

| id | player | date | start | timing | own merchants en route | own fleets en route | AI merchants en route | AI fleets en route | AI fleet targets | version | mods | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S01 | VEN | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S02 | ENG | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S03 | FRA | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S04 | CAS | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S05 | POR | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S06 | HAB | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S07 | BUR | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S08 | HSA | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S09 | GEN | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S10 | RAG | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S11 | POL | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S12 | NOV | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S13 | SWE | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S14 | TUR | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S15 | MAM | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S16 | TIM | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S17 | MOS | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S18 | KAZ | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S19 | CRI | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S20 | MNG | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S21 | ASK | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S22 | KOR | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S23 | VIJ | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S24 | BAH | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S25 | DLH | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S26 | AYU | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S27 | MAJ | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S28 | ETH | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S29 | MAL | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S30 | KON | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S31 | ZAN | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S32 | KTS | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S33 | AZT | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S34 | CSU | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S35 | ONO | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S36 | TUR | 1500.1.1 | 1500.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S37 | TUR | 1600.1.1 | 1600.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S38 | TUR | 1700.1.1 | 1700.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S39 | SPA | 1550.1.1 | 1550.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| S40 | POR | 1600.1.1 | 1600.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S41 | NED | 1650.1.1 | 1650.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S42 | GBR | 1750.1.1 | 1750.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S43 | ENG | 1526.1.1 | 1526.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S44 | GEN | 1550.1.1 | 1550.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S45 | DLH | 1526.1.1 | 1526.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S46 | PER | 1526.1.1 | 1526.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S47 | SON | 1550.1.1 | 1550.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S48 | BUK | 1526.1.1 | 1526.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S49 | TUN | 1550.1.1 | 1550.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S50 | KOR | 1550.1.1 | 1550.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S51 | VEN | 1600.1.1 | 1600.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S52 | ENG | 1644.11.11 | 1644.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S53 | NED | 1624.11.11 | 1624.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S54 | RUS | 1614.11.11 | 1614.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S55 | MNG | 1634.11.11 | 1634.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S56 | KON | 1650.11.11 | 1650.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S57 | OMA | 1650.11.11 | 1650.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S58 | BIJ | 1630.11.11 | 1630.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S59 | GEN | 1700.1.11 | 1700.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S60 | VEN | 1700.1.11 | 1700.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S61 | RUS | 1700.11.11 | 1700.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S62 | PRU | 1744.11.11 | 1744.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S63 | QNG | 1744.11.11 | 1744.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S64 | MYS | 1761.1.11 | 1761.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S65 | OMA | 1785.1.11 | 1785.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S66 | USA | 1785.1.11 | 1785.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S67 | GBR | 1800.1.11 | 1800.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S68 | RUS | 1810.1.11 | 1810.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S69 | FRA | 1800.1.11 | 1800.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S70 | HAB | 1810.1.11 | 1810.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S71 | QNG | 1820.1.11 | 1820.1.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S72 | USA | 1821.1.1 | 1821.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S73 | TUR | 1821.1.1 | 1821.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S74 | OMA | 1821.1.1 | 1821.1.1 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S75 | FRA | 1744.11.11 | 1744.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S76 | NED | 1744.11.11 | 1744.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S77 | POR | 1744.11.11 | 1744.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S78 | SPA | 1744.11.11 | 1744.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | vanilla | delete |
| S79 | TUR | 1665.4.22 | 1444.11.11 | mid_month | 0 | 0 | 3 | 8 | english_channel 2, panama 1, baltic_sea 1, carribean_trade 1 | 1.37.5 | mods-7ec58e40 | delete |
| S80 | TUR | 1682.4.18 | 1444.11.11 | mid_month | 0 | 0 | 1 | 3 | sevilla 1, malacca 1, gulf_of_siam 1 | 1.37.5 | mods-7ec58e40 | delete |
| U01 | TUR | 1682.4.18 | 1444.11.11 | mid_month | 0 | 0 | 1 | 3 | sevilla 1, malacca 1, gulf_of_siam 1 | 1.37.5 | mods-7ec58e40 | delete |
| U02 | TUR | 1665.4.22 | 1444.11.11 | mid_month | 0 | 0 | 3 | 8 | english_channel 2, panama 1, baltic_sea 1, carribean_trade 1 | 1.37.5 | mods-7ec58e40 | delete |
| U03 | TUR | 1691.1.9 | 1444.11.11 | mid_month | 0 | 0 | 1 | 1 | hangzhou 1 | 1.37.5 | mods-7ec58e40 | delete |
| U04 | TUR | 1691.11.1 | 1444.11.11 | tick_day | 0 | 0 | 0 | 1 | ganges_delta 1 | 1.37.5 | mods-7ec58e40 | KEEP |
| U05 | TUR | 1693.4.15 | 1444.11.11 | mid_month | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| U06 | TUR | 1696.3.25 | 1444.11.11 | mid_month | 0 | 0 | 1 | 1 | comorin_cape 1 | 1.37.5 | mods-7ec58e40 | delete |
| U07 | VEN | 1444.11.11 | 1444.11.11 | pre_first_tick | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| U08 | VEN | 1444.11.14 | 1444.11.11 | pre_first_tick | 0 | 0 | 234 | 1 | beijing 1 | 1.37.5 | mods-7ec58e40 | delete |
| U09 | VEN | 1444.11.30 | 1444.11.11 | pre_first_tick | 0 | 0 | 51 | 6 | north_sea 1, gulf_of_aden 1, safi 1, comorin_cape 1 | 1.37.5 | mods-7ec58e40 | delete |
| U10 | VEN | 1444.12.1 | 1444.11.11 | tick_day | 0 | 0 | 52 | 8 | polynesia_node 4, comorin_cape 2, lubeck 1, zanzibar 1 | 1.37.5 | mods-7ec58e40 | KEEP |
| U11 | VEN | 1444.12.2 | 1444.11.11 | mid_month | 0 | 0 | 54 | 4 | polynesia_node 2, north_sea 1, comorin_cape 1 | 1.37.5 | mods-7ec58e40 | delete |
| U12 | VEN | 1444.12.11 | 1444.11.11 | mid_month | 0 | 0 | 20 | 3 | gulf_of_aden 1, gujarat 1, malacca 1 | 1.37.5 | mods-7ec58e40 | delete |
| U13 | VEN | 1444.12.31 | 1444.11.11 | mid_month | 0 | 0 | 6 | 3 | gujarat 2, malacca 1 | 1.37.5 | mods-7ec58e40 | delete |
| U14 | VEN | 1445.1.1 | 1444.11.11 | tick_day | 0 | 0 | 5 | 3 | gujarat 2, malacca 1 | 1.37.5 | mods-7ec58e40 | KEEP |
| U15 | VEN | 1445.1.2 | 1444.11.11 | mid_month | 0 | 0 | 5 | 3 | gujarat 2, malacca 1 | 1.37.5 | mods-7ec58e40 | delete |
| U16 | VEN | 1445.1.15 | 1444.11.11 | mid_month | 0 | 0 | 1 | 1 | gujarat 1 | 1.37.5 | mods-7ec58e40 | delete |
| U17 | VEN | 1445.1.24 | 1444.11.11 | mid_month | 0 | 0 | 2 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| U18 | VEN | 1445.1.30 | 1444.11.11 | mid_month | 0 | 0 | 1 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| U19 | VEN | 1445.1.31 | 1444.11.11 | mid_month | 0 | 0 | 1 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| U20 | VEN | 1445.2.1 | 1444.11.11 | tick_day | 0 | 0 | 1 | 0 |  | 1.37.5 | mods-7ec58e40 | KEEP |
| U21 | VEN | 1445.2.3 | 1444.11.11 | mid_month | 0 | 0 | 1 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| U22 | VEN | 1445.2.10 | 1444.11.11 | mid_month | 0 | 0 | 1 | 1 | comorin_cape 1 | 1.37.5 | mods-7ec58e40 | delete |
| U23 | VEN | 1445.2.17 | 1444.11.11 | mid_month | 0 | 0 | 0 | 1 | comorin_cape 1 | 1.37.5 | mods-7ec58e40 | delete |
| U24 | VEN | 1445.2.28 | 1444.11.11 | mid_month | 0 | 0 | 0 | 1 | gulf_of_aden 1 | 1.37.5 | mods-7ec58e40 | delete |
| U25 | VEN | 1445.3.1 | 1444.11.11 | tick_day | 0 | 0 | 0 | 1 | gulf_of_aden 1 | 1.37.5 | mods-7ec58e40 | KEEP |
| U26 | VEN | 1445.3.31 | 1444.11.11 | mid_month | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
| U27 | VEN | 1445.4.1 | 1444.11.11 | tick_day | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | KEEP |
| U28 | VEN | 1445.5.1 | 1444.11.11 | tick_day | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | KEEP |
| U29 | VEN | 1445.6.1 | 1444.11.11 | tick_day | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | KEEP |
| U30 | VEN | 1445.7.2 | 1444.11.11 | mid_month | 0 | 0 | 0 | 0 |  | 1.37.5 | mods-7ec58e40 | delete |
