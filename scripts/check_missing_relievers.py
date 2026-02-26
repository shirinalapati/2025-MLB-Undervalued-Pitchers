#!/usr/bin/env python3
"""Parse user's relief pitcher list and check which are missing from pitchers.json."""

import json
import re
from pathlib import Path

# User's relief pitcher list (tab-separated: Rank, PlayerInfo, IP, K, SV, BS, HD, ERA, WHIP, ER, H, BB, HR, G, W, L, Rost%)
USER_LIST = """
28	Nick Martinez (TB - SP,RP)	165.2	116	0	0	5	4.45	1.21	82	158	42	22	40	11	14	2%
81	Kyle Hendricks (SP,RP) FA	164.2	114	0	0	0	4.76	1.28	87	167	43	25	31	8	10	5%
22	Colin Rea (CHC - SP,RP)	159.1	127	1	0	0	3.95	1.24	70	153	44	20	32	11	7	1%
156	Chris Paddack (MIA - SP,RP)	158.0	112	1	0	0	5.35	1.28	94	166	37	31	33	5	12	0%
8	Quinn Priester (MIL - SP,RP)	157.1	132	0	0	0	3.32	1.24	58	145	50	18	29	13	3	40%
10	Ryne Nelson (ARI - SP,RP)	154.0	132	1	1	1	3.39	1.07	58	124	41	17	33	7	3	37%
252	Charlie Morton (SP,RP) FA	142.0	149	0	0	0	5.83	1.58	92	152	72	23	33	9	11	14%
89	Michael Lorenzen (COL - SP,RP)	141.2	127	0	0	1	4.64	1.33	73	149	39	25	27	7	11	1%
141	Sean Burke (CWS - SP,RP)	134.1	133	0	0	0	4.29	1.45	64	132	63	23	28	4	11	1%
98	Brad Lord (WSH - SP,RP)	130.2	108	0	0	7	4.34	1.29	63	126	43	17	48	5	10	0%
139	Taijuan Walker (PHI - SP,RP)	123.2	86	1	2	2	4.08	1.41	56	132	42	21	34	5	8	1%
64	Janson Junk (MIA - SP,RP)	110.0	77	1	0	0	4.17	1.14	51	112	13	8	21	6	4	0%
223	Ben Brown (CHC - SP,RP)	106.1	121	1	1	1	5.92	1.44	70	121	32	18	25	5	8	1%
23	Eric Lauer (TOR - SP,RP)	104.2	102	0	0	1	3.18	1.11	37	90	26	15	28	9	2	2%
144	Aaron Civale (ATH - SP,RP)	102.0	88	1	0	0	4.85	1.26	55	96	33	16	23	4	9	0%
212	Ryan Gusto (MIA - SP,RP)	101.2	97	0	0	0	5.67	1.47	64	113	36	17	27	7	7	0%
35	Mike Vasil (CWS - SP,RP)	101.0	82	4	2	3	2.50	1.25	28	74	52	8	47	5	3	1%
86	Carmen Mlodzinski (PIT - SP,RP)	99.0	89	0	1	3	3.55	1.30	39	102	27	8	34	5	8	1%
185	Tyler Alexander (TEX - SP,RP)	97.2	82	1	2	4	4.98	1.39	54	106	30	9	52	5	14	0%
116	Mike Burrows (HOU - SP,RP)	96.0	97	0	0	1	3.94	1.23	42	87	31	13	23	2	4	5%
47	Joey Cantillo (CLE - SP,RP)	95.1	108	1	0	1	3.21	1.26	34	78	42	10	34	5	3	8%
90	Sean Newcomb (CWS - SP,RP)	92.1	91	2	0	4	2.73	1.35	28	94	31	5	48	2	5	0%
166	Keider Montero (DET - SP,RP)	90.2	72	0	0	0	4.37	1.39	44	95	31	16	20	5	3	0%
177	J.T. Ginn (ATH - SP,RP)	90.1	99	0	0	1	5.08	1.35	51	91	31	17	23	4	7	0%
216	Emerson Hancock (SEA - SP,RP)	90.0	64	0	0	0	4.90	1.38	49	93	31	15	22	4	5	0%
107	Michael Soroka (ARI - SP,RP)	89.2	95	0	0	1	4.52	1.13	45	72	29	12	22	3	8	1%
75	Kyle Leahy (STL - RP)	88.0	80	1	4	18	3.07	1.23	30	80	28	5	62	4	2	1%
203	Colton Gordon (HOU - SP,RP)	86.0	72	1	0	0	5.34	1.42	51	103	19	21	20	6	4	0%
93	Jacob Latz (TEX - SP,RP)	85.2	76	1	0	2	2.84	1.24	27	69	37	7	33	2	0	1%
266	Mitch Spence (KC - SP,RP)	84.2	66	1	0	4	5.10	1.44	48	96	26	16	32	3	6	0%
82	Jimmy Herget (COL - RP)	83.1	81	0	1	9	2.48	1.18	23	72	26	6	59	1	2	0%
254	Valente Bellozo (COL - SP,RP) NRI	81.1	54	0	1	1	4.65	1.33	42	85	23	15	32	1	4	0%
148	Spencer Bivens (SF - RP)	81.0	61	3	0	4	4.11	1.35	37	84	25	6	54	4	3	0%
33	Eduard Bazardo (SEA - RP)	78.2	82	0	1	12	2.52	1.02	22	53	27	9	73	5	0	1%
61	Tyler Holton (DET - SP,RP)	78.2	64	0	5	17	3.66	1.04	32	65	17	15	70	6	5	3%
83	Tyler Phillips (MIA - RP)	77.2	52	4	0	8	2.78	1.13	24	64	24	8	54	2	1	0%
112	Ben Casparius (LAD - SP,RP)	77.2	71	2	0	13	4.64	1.27	40	78	21	8	46	7	5	1%
36	Tyler Rogers (TOR - RP)	77.1	48	0	2	32	1.98	0.94	17	66	7	4	81	4	6	11%
192	Jason Alexander (HOU - SP,RP)	77.1	65	1	0	0	4.77	1.37	41	80	26	15	18	4	2	0%
147	Carlos Vargas (SEA - RP)	77.0	54	1	7	14	3.97	1.34	34	80	23	10	70	5	5	0%
57	Steven Matz (TB - RP)	76.2	59	2	4	13	3.05	1.08	26	72	11	8	53	5	2	1%
48	Jack Dreyer (LAD - SP,RP)	76.1	74	4	2	10	2.95	1.05	25	56	24	4	67	3	2	2%
99	Jose A. Ferrer (SEA - RP)	76.1	71	11	4	21	4.48	1.27	38	81	16	5	72	4	4	2%
30	Edwin Uceta (TB - RP)	76.0	103	1	5	21	3.79	1.17	32	62	27	11	70	10	3	21%
26	Abner Uribe (MIL - RP)	75.1	90	7	2	37	1.67	1.04	14	51	27	4	75	3	2	64%
18	Shawn Armstrong (CLE - RP)	74.0	74	9	3	12	2.31	0.80	19	39	20	5	71	4	3	2%
9	Adrian Morejon (SD - RP)	73.2	70	3	4	20	2.20	0.91	18	50	17	2	75	13	6	10%
12	Cade Smith (CLE - RP)	73.2	104	16	6	19	2.93	1.00	24	55	19	4	76	8	5	99%
55	Tony Santillan (CIN - RP)	73.2	75	7	4	33	2.44	1.11	20	53	29	7	80	1	5	4%
21	Ronny Henriquez (MIA - RP) IL60	73.0	98	7	4	26	2.22	1.10	18	53	27	8	69	7	1	2%
52	Jeremiah Estrada (SD - RP)	73.0	108	3	3	30	3.45	1.16	28	58	27	12	77	4	5	15%
87	Yariel Rodriguez (TOR - RP) NRI	73.0	66	2	1	14	3.08	1.15	25	50	34	8	66	3	2	0%
79	Tyler Kinley (ATL - RP)	72.2	73	3	3	14	3.96	1.18	32	53	33	6	73	6	3	0%
84	Louis Varland (TOR - RP)	72.2	75	0	2	22	2.97	1.20	24	65	22	6	74	4	3	2%
27	Garrett Whitlock (BOS - RP)	72.0	91	1	4	24	2.25	1.08	18	54	24	2	62	7	3	13%
125	Cole Sands (MIN - SP,RP)	72.0	64	3	4	13	4.50	1.17	36	65	19	7	69	4	6	1%
40	Steven Okert (HOU - RP)	71.2	84	1	2	10	3.01	0.89	24	45	19	6	68	3	2	1%
111	Wandy Peralta (SD - RP)	71.2	63	0	1	4	3.27	1.35	26	67	30	5	71	6	1	0%
31	Bryan Abreu (HOU - RP)	71.0	105	7	5	25	2.28	1.15	18	51	31	4	70	3	4	61%
60	Lake Bachar (MIA - RP)	71.0	75	3	1	6	3.93	1.20	31	55	30	10	53	8	2	0%
17	Dennis Santana (PIT - RP)	70.1	60	16	3	13	2.18	0.87	17	44	17	5	70	4	5	49%
174	Hoby Milner (CHC - RP)	70.1	58	0	4	18	4.09	1.28	32	69	21	5	73	3	4	0%
4	Jhoan Duran (PHI - RP)	70.0	80	32	5	1	2.06	1.10	16	58	19	3	72	7	6	99%
3	Robert Suarez (ATL - RP)	69.2	75	40	5	0	2.97	0.90	23	47	16	6	70	4	6	68%
29	Brad Keller (PHI - RP)	69.2	75	3	3	25	2.07	0.96	16	45	22	4	68	4	2	3%
91	Braxton Ashcraft (PIT - SP,RP)	69.2	71	0	1	4	2.71	1.25	21	63	24	3	26	4	4	10%
130	Grant Anderson (MIL - RP)	69.2	74	0	3	6	3.23	1.26	25	59	29	8	66	2	6	0%
189	Brandon Eisert (CWS - SP,RP)	69.2	74	2	3	9	4.39	1.44	34	75	25	12	72	3	8	0%
13	Emilio Pagan (CIN - RP)	68.2	81	32	6	2	2.88	0.92	22	41	22	10	70	2	4	86%
25	Will Vest (DET - RP)	68.2	75	23	7	3	3.01	1.21	23	61	22	4	64	6	5	18%
85	Bryan Baker (TB - RP)	68.2	83	3	6	19	4.06	1.11	31	59	17	13	73	4	4	1%
76	Dylan Lee (ATL - RP)	68.1	76	2	7	19	3.29	0.98	25	53	14	13	74	2	4	1%
104	Brendon Little (TOR - RP)	68.1	91	1	3	30	3.03	1.39	23	50	45	2	79	4	2	1%
133	Scott Barlow (ATH - RP)	68.1	75	1	1	16	4.21	1.39	32	50	45	8	75	6	3	0%
14	Jeff Hoffman (TOR - RP)	68.0	84	33	7	0	4.37	1.19	33	54	27	15	71	9	7	87%
44	Bryan King (HOU - RP)	68.0	69	2	3	27	2.78	1.04	21	60	11	10	68	5	4	2%
120	Daniel Lynch (KC - RP)	67.2	45	1	0	7	3.06	1.36	23	66	26	8	57	6	2	0%
226	Brent Suter (LAA - SP,RP)	67.2	53	0	1	0	4.52	1.27	34	68	18	11	48	1	2	0%
15	Raisel Iglesias (ATL - RP)	67.1	73	29	5	2	3.21	0.98	24	50	16	8	70	4	6	93%
53	Tanner Banks (PHI - RP)	67.1	61	1	3	10	3.21	1.02	24	57	12	9	69	6	2	1%
56	Greg Weissert (BOS - RP)	67.0	57	4	9	17	2.82	1.16	21	57	21	6	72	6	6	1%
108	Tim Hill (NYY - RP)	67.0	37	0	0	15	3.09	1.09	23	57	16	8	70	4	4	0%
153	Jose Butto (SF - SP,RP)	67.0	58	1	4	6	3.90	1.40	29	62	32	4	55	5	3	1%
41	Aaron Ashby (MIL - RP)	66.2	76	3	0	6	2.16	1.17	16	54	24	3	43	5	2	1%
103	Hunter Gaddis (CLE - RP)	66.2	73	3	4	35	3.11	1.19	23	58	21	8	73	2	2	7%
115	Jakob Junis (TEX - RP)	66.2	55	0	0	6	2.97	1.23	22	64	18	5	57	4	1	0%
117	Justin Wrobleski (LAD - RP)	66.2	76	2	0	7	4.32	1.23	32	65	17	6	24	5	5	1%
2	Edwin Diaz (LAD - RP)	66.1	98	28	3	0	1.63	0.86	12	36	21	4	62	6	3	99%
6	Carlos Estevez (KC - RP)	66.0	54	42	6	0	2.45	1.06	18	48	22	5	67	4	5	91%
59	Jared Koenig (MIL - RP)	66.0	68	2	2	27	2.86	1.17	21	57	20	6	72	6	1	1%
67	Jacob Webb (CHC - RP)	66.0	58	1	2	7	3.00	1.03	22	49	19	10	55	5	4	1%
137	Enyel De Los Santos (HOU - RP)	66.0	62	0	2	6	4.36	1.29	32	61	24	7	65	6	3	0%
160	Griffin Jax (TB - RP)	66.0	99	0	6	28	4.23	1.29	31	64	21	7	73	1	7	58%
221	Hayden Birdsong (SF - SP,RP)	65.2	68	0	0	3	4.80	1.49	35	61	37	10	21	4	4	1%
34	Jason Adam (SD - RP)	65.1	70	0	2	29	1.93	1.15	14	50	25	4	65	8	4	9%
63	Camilo Doval (NYY - RP)	65.1	72	16	6	10	3.58	1.32	26	51	35	4	69	4	3	5%
113	Caleb Ferguson (CIN - RP)	65.1	51	0	5	14	3.58	1.16	26	54	22	2	70	5	4	0%
123	Graham Ashcraft (CIN - RP)	65.1	64	0	6	23	3.99	1.42	29	68	25	2	62	8	5	1%
77	Justin Sterner (ATH - RP)	65.0	70	0	6	16	3.18	1.05	23	47	21	10	59	4	3	4%
101	Anthony Banda (MIN - RP)	65.0	61	0	1	12	3.18	1.22	23	45	34	8	71	5	1	0%
136	Kolby Allard (CLE - SP,RP) NRI	65.0	42	0	0	4	2.63	1.20	19	64	14	5	33	2	2	0%
51	Luke Weaver (NYM - RP)	64.2	72	8	4	21	3.62	1.02	26	46	20	10	64	4	4	7%
145	Hogan Harris (ATH - RP)	64.2	65	4	0	3	3.34	1.35	24	54	33	5	48	2	1	0%
167	Angel Zerpa (MIL - RP)	64.2	58	0	4	14	4.18	1.38	30	67	22	7	69	5	2	0%
73	Jordan Leasure (CWS - RP)	64.1	81	7	5	14	3.78	1.21	27	48	30	12	68	5	6	2%
71	Robert Garcia (TEX - RP)	64.0	68	9	7	15	2.95	1.25	21	58	22	8	71	4	8	19%
134	John Schreiber (KC - RP)	64.0	62	1	4	23	3.80	1.19	27	57	19	10	74	3	3	0%
163	Ryan Yarbrough (NYY - SP,RP)	64.0	55	1	0	0	4.36	1.20	31	58	19	13	19	3	1	1%
109	Reid Detmers (LAA - RP)	63.2	80	3	5	13	3.96	1.30	28	58	25	6	61	5	3	9%
100	Keegan Akin (BAL - SP,RP)	63.1	59	8	6	16	3.41	1.37	24	54	33	10	64	5	4	1%
175	Yuki Matsui (SD - RP)	63.1	61	1	0	3	3.98	1.34	28	52	33	10	61	3	1	0%
97	Brant Hurter (DET - SP,RP)	63.0	68	2	0	5	2.43	1.33	17	57	27	4	43	4	3	1%
114	Huascar Brazoban (NYM - SP,RP)	63.0	57	2	4	12	3.57	1.24	25	51	27	6	52	5	2	0%
180	Tommy Kahnle (RP) FA	63.0	50	9	5	16	4.43	1.30	31	51	31	8	66	1	5	0%
11	David Bednar (NYY - RP)	62.2	86	27	3	4	2.30	1.04	16	46	19	4	64	6	5	96%
102	Seranthony Dominguez (CWS - RP)	62.2	79	2	3	20	3.30	1.28	23	44	36	5	67	4	4	28%
239	Yoendrys Gomez (TB - SP,RP)	62.2	58	1	0	0	5.17	1.39	36	60	27	12	21	3	3	0%
5	Andres Munoz (SEA - RP)	62.1	83	38	7	0	1.73	1.03	12	36	28	2	64	3	3	99%
72	Matt Strahm (KC - RP)	62.1	70	6	4	22	2.74	1.07	19	47	20	5	66	2	3	5%
39	Gabe Speier (SEA - RP)	62.0	82	0	6	24	2.61	0.87	18	43	11	5	76	4	3	3%
49	Devin Williams (NYM - RP)	62.0	90	18	4	15	4.94	1.15	34	46	25	5	67	4	6	96%
20	Mason Miller (SD - RP)	61.2	104	22	4	10	2.63	0.92	18	29	28	5	60	1	2	99%
95	Brock Burke (CIN - RP)	61.2	52	0	5	15	3.36	1.23	23	58	18	8	69	7	1	0%
1	Aroldis Chapman (BOS - RP)	61.1	85	32	2	4	1.17	0.70	8	28	15	3	67	5	3	98%
45	Phil Maton (CHC - RP)	61.1	81	5	5	22	2.79	1.06	19	42	23	3	63	4	5	2%
50	Garrett Cleavinger (TB - RP)	61.1	82	2	4	21	2.35	0.95	16	40	18	9	67	2	6	3%
54	Lucas Erceg (KC - RP)	61.1	48	2	5	22	2.64	1.17	18	54	18	4	61	8	4	2%
66	Ryan Walker (SF - RP)	61.1	60	17	7	9	4.11	1.26	28	59	18	4	68	5	7	61%
157	Juan Mejia (COL - RP)	61.1	68	1	3	12	3.96	1.24	27	51	25	6	55	2	2	0%
65	JoJo Romero (STL - RP)	61.0	55	8	1	24	2.07	1.25	14	47	29	2	65	4	6	6%
211	Sean Manaea (NYM - SP,RP)	60.2	75	0	0	0	5.64	1.22	38	62	12	13	15	2	4	16%
24	Pete Fairbanks (MIA - RP)	60.1	59	27	5	0	2.83	1.04	19	45	18	7	61	4	5	86%
38	Matt Svanson (STL - RP)	60.1	68	0	0	5	1.94	0.88	13	33	20	3	39	4	0	1%
68	Calvin Faucher (MIA - RP)	60.1	59	15	5	7	3.28	1.28	22	53	24	8	65	4	4	1%
218	Gregory Soto (PIT - RP)	60.1	70	1	1	23	4.18	1.43	28	62	24	4	70	1	5	1%
231	Rafael Montero (NYY - RP) NRI	60.1	58	0	1	8	4.48	1.31	30	42	37	5	59	1	2	0%
78	Orion Kerkering (PHI - RP)	60.0	65	4	7	19	3.30	1.37	22	55	27	6	69	8	4	2%
165	Brenan Hanifee (DET - RP)	60.0	40	0	1	10	3.00	1.32	20	65	14	3	54	3	3	0%
215	Justin Topa (MIN - RP)	60.0	49	4	4	4	3.90	1.43	26	68	18	2	54	1	5	0%
42	Alex Vesia (LAD - RP)	59.2	80	5	4	26	3.02	0.99	20	37	22	9	68	4	2	6%
16	Kenley Jansen (DET - RP)	59.0	57	29	1	0	2.75	0.97	18	38	19	8	62	5	4	85%
121	Pierce Johnson (CIN - RP)	59.0	59	1	3	16	3.05	1.20	20	52	19	8	65	3	3	1%
69	Caleb Thielbar (CHC - RP)	58.0	56	1	3	25	2.64	0.88	17	38	13	5	67	3	4	1%
183	Tyler Ferguson (ATH - RP)	58.0	54	2	3	12	4.66	1.33	30	43	34	4	56	4	2	0%
257	Yennier Cano (BAL - RP)	58.0	53	2	5	17	5.12	1.48	33	62	24	7	65	3	7	0%
110	Jalen Beeks (RP) FA	57.1	47	1	2	14	3.77	1.08	24	42	20	6	61	5	3	0%
32	Kyle Finnegan (DET - RP)	57.0	55	24	7	3	3.47	1.11	22	45	18	4	56	4	4	8%
96	Tanner Scott (LAD - RP)	57.0	60	23	10	8	4.74	1.26	30	54	18	11	61	1	4	6%
129	Ian Seymour (TB - SP,RP)	57.0	64	0	1	0	3.79	1.19	24	49	19	5	19	4	3	8%
158	Ryan Zeferjahn (LAA - RP)	57.0	73	2	6	17	4.74	1.47	30	49	35	12	62	6	5	0%
88	Nick Mears (KC - RP)	56.2	46	1	6	17	3.49	0.97	22	42	13	7	63	5	3	0%
197	Tristan Beck (SF - RP)	56.2	41	2	0	3	4.61	1.11	29	47	16	7	31	1	0	0%
126	Ryan Helsley (BAL - RP)	56.0	63	21	9	1	4.82	1.55	30	62	25	8	58	3	4	87%
255	Ryne Stanek (STL - RP)	56.0	58	3	6	11	5.46	1.57	34	56	32	7	65	4	6	0%
118	Taylor Clarke (ARI - RP)	55.1	44	1	1	5	3.25	0.85	20	38	9	8	51	1	1	0%
151	Reed Garrett (NYM - RP) IL60	55.1	64	3	7	20	3.90	1.32	24	47	26	5	58	3	6	0%
168	Steven Wilson (TB - RP)	55.1	51	2	7	10	3.42	1.30	21	50	22	7	59	2	2	0%
190	Luis Garcia (NYM - RP)	55.1	48	2	1	12	3.09	1.45	19	54	26	2	58	2	2	0%
278	Jake Bird (NYY - RP)	55.1	66	0	6	10	5.69	1.55	35	61	25	7	48	4	2	0%
119	Matt Festa (CLE - RP)	54.2	56	0	2	12	4.12	1.08	25	44	15	4	63	5	4	0%
122	Cade Gibson (MIA - RP)	54.2	43	0	2	5	2.63	1.19	16	44	21	3	44	4	5	0%
170	Aaron Bummer (ATL - RP)	54.1	51	0	0	2	3.81	1.25	23	51	17	3	42	3	2	0%
74	Andrew Kittredge (BAL - RP)	53.0	64	5	1	15	3.40	0.98	20	41	11	7	54	4	3	2%
7	Josh Hader (HOU - RP)	52.2	76	28	1	0	2.05	0.85	12	29	16	8	48	6	2	95%
46	Daniel Palencia (CHC - RP)	52.2	61	22	3	6	2.91	1.14	17	44	16	5	54	1	6	82%
132	Mason Fluharty (TOR - RP)	52.2	56	1	2	6	4.44	1.14	26	36	24	6	55	5	2	0%
243	Cole Henry (WSH - RP)	52.2	52	2	0	10	4.27	1.42	25	43	32	7	57	1	2	0%
248	Joe Boyle (TB - SP,RP)	52.0	58	0	0	0	4.67	1.35	27	42	28	6	13	1	4	1%
143	Brennan Bernardino (COL - SP,RP)	51.2	43	1	0	2	3.14	1.26	18	39	26	1	55	4	3	0%
152	Tyler Gilbert (CWS - SP,RP)	51.0	49	1	0	5	3.88	1.25	22	40	24	5	46	4	2	0%
176	Luke Jackson (RP) FA	51.0	38	9	2	4	4.06	1.35	23	41	28	4	52	2	5	0%
43	Randy Rodriguez (SF - RP) IL60	50.2	67	4	3	13	1.78	0.89	10	34	11	4	50	3	5	1%
70	Bennett Sousa (HOU - RP)	50.2	59	4	2	7	2.84	1.03	16	37	15	4	44	5	1	1%
105	Victor Vodnik (COL - RP)	50.2	49	10	5	7	2.84	1.40	16	45	26	4	52	4	3	3%
182	Taylor Rogers (MIN - RP)	50.2	53	0	2	10	3.38	1.38	19	47	23	7	57	3	2	1%
234	Tobias Myers (NYM - SP,RP)	50.2	38	0	0	1	3.55	1.36	20	54	15	5	22	1	2	1%
58	Braydon Fisher (TOR - RP)	50.0	62	0	1	5	2.70	1.02	15	32	19	4	52	7	0	1%
94	Anthony Bender (MIA - RP)	50.0	42	4	3	19	2.16	1.08	12	33	21	3	51	3	5	1%
106	Drew Pomeranz (LAA - SP,RP)	49.2	57	1	2	14	2.17	1.07	12	38	15	5	57	2	2	1%
250	Casey Legumina (SEA - RP)	49.2	55	0	0	3	5.62	1.45	31	47	25	7	48	4	6	0%
230	Jackson Jobe (DET - SP,RP) IL60	49.0	39	0	0	0	4.22	1.49	23	46	27	7	10	4	1	2%
164	Justin Wilson (RP) FA	48.1	57	0	4	19	3.35	1.41	18	48	20	3	61	4	1	0%
196	Mark Leiter Jr. (ATH - RP)	48.1	54	2	4	14	5.03	1.55	27	58	17	5	59	6	7	1%
92	Riley O'Brien (STL - RP)	48.0	45	6	3	6	2.06	1.15	11	33	22	2	42	3	1	7%
124	Fernando Cruz (NYY - RP)	48.0	72	2	1	16	3.56	1.19	19	33	24	5	49	3	4	2%
128	Isaac Mattson (PIT - RP)	47.2	45	0	3	12	2.45	1.13	13	35	19	4	44	3	3	0%
209	Lou Trivino (PHI - RP) NRI	47.2	37	0	2	5	3.97	1.34	21	46	18	6	47	3	2	0%
37	Emmanuel Clase (CLE - RP) OUT	47.1	47	24	5	1	3.23	1.23	17	46	12	2	48	5	3	1%
135	Matt Brash (SEA - RP)	47.1	58	4	1	21	2.47	1.23	13	40	18	4	53	1	3	5%
173	David Morgan (SD - RP)	47.1	50	0	0	1	2.66	1.23	14	35	23	4	41	1	2	0%
19	Trevor Megill (MIL - RP)	47.0	60	30	6	0	2.49	1.13	13	36	17	3	50	6	3	88%
241	Connor Brogdon (CLE - RP)	47.0	49	0	0	4	5.36	1.32	28	44	18	11	43	3	2	0%
201	Dietrich Enns (BAL - SP,RP)	46.1	49	2	0	4	4.27	1.40	22	50	15	6	24	3	3	0%
62	Shelby Miller (CHC - RP)	46.0	54	10	5	9	2.74	1.04	14	33	15	5	48	4	3	1%
242	Kaleb Ort (LAA - RP) NRI	46.0	49	1	0	3	4.89	1.35	25	35	27	8	49	2	2	0%
131	Troy Melton (DET - SP,RP)	45.2	36	0	0	4	2.76	1.01	14	31	15	7	16	3	2	2%
181	Steven Cruz (KC - RP)	45.2	38	0	0	9	3.74	1.18	19	36	18	5	47	3	1	0%
149	Chase Shugart (PHI - RP)	45.0	31	0	3	5	3.40	1.11	17	33	17	6	35	4	3	0%
229	Mason Englert (TB - RP)	44.2	44	0	0	1	3.83	1.21	19	43	11	4	29	0	1	0%
208	Jonathan Bowlan (PHI - RP)	44.1	46	0	0	2	3.86	1.22	19	37	17	6	34	1	2	0%
296	Scott Blewett (STL - RP) NRI	44.1	35	0	0	0	5.48	1.42	27	45	18	9	26	3	0	0%
142	Chris Flexen (RP) FA	43.2	22	1	0	0	3.09	1.15	15	38	12	7	21	5	1	0%
300	Chad Green (RP) FA	43.2	35	1	0	7	5.56	1.47	27	51	13	14	45	3	2	0%
140	Danny Coulombe (RP) FA	43.0	43	2	0	9	2.30	1.16	11	32	18	3	55	2	1	0%
246	Kyle Hart (SD - SP,RP)	43.0	37	0	0	2	5.86	1.19	28	38	13	9	20	3	3	0%
232	Tim Herrin (CLE - RP)	42.2	45	0	2	15	4.85	1.57	23	37	30	5	54	5	4	0%
161	Chris Martin (TEX - RP)	42.1	43	2	3	13	2.98	1.20	14	43	8	6	49	2	6	1%
204	Elvis Alvarado (ATH - RP)	42.1	50	0	1	4	3.19	1.32	15	34	22	6	37	1	1	0%
256	Trent Thornton (CHC - RP) NRI	42.1	32	0	1	5	4.68	1.30	22	41	14	6	33	2	0	0%
146	Cole Winn (TEX - RP)	41.2	35	0	0	4	1.51	0.96	7	23	17	3	33	0	1	0%
200	Eric Orze (MIN - RP)	41.2	40	3	1	1	3.02	1.37	14	38	19	4	33	1	1	0%
188	Kirby Yates (LAA - RP)	41.1	52	3	2	15	5.23	1.33	24	38	17	9	50	4	3	4%
205	Ryan Thompson (ARI - RP)	41.1	36	1	3	17	3.92	1.33	18	42	13	4	48	3	2	0%
285	Max Lazar (PHI - RP)	41.1	26	1	0	1	4.79	1.28	22	41	12	7	36	1	1	0%
198	Kody Funderburk (MIN - RP)	41.0	40	1	0	7	3.51	1.51	16	44	18	2	39	4	1	0%
214	Ian Hamilton (ATL - RP)	40.0	42	0	0	4	4.28	1.25	19	28	22	5	36	2	1	0%
159	Michael Kelly (ATH - RP)	39.2	29	2	1	7	2.95	1.26	13	31	19	5	42	4	4	0%
237	Seth Halvorsen (COL - RP)	39.2	36	11	3	4	4.99	1.56	22	41	21	7	42	1	2	1%
178	Jack Perkins (ATH - RP)	38.2	37	3	0	1	4.19	1.16	18	27	18	4	12	3	2	0%
207	DL Hall (MIL - SP,RP)	38.2	27	0	0	1	3.49	1.06	15	24	17	2	20	1	0	0%
267	Anthony DeSclafani (SP,RP) FA	38.2	36	2	0	1	5.12	1.27	22	37	12	11	13	1	2	0%
260	Joey Lucchesi (RP) FA	38.1	31	0	0	6	3.76	1.23	16	35	12	4	38	0	1	0%
299	Kyle Nicolas (PIT - RP)	38.0	34	0	1	3	4.74	1.37	20	34	18	3	31	1	2	0%
172	Brock Stewart (LAD - RP)	37.2	44	0	1	16	2.63	1.19	11	32	13	3	43	2	2	0%
171	Chase Lee (TOR - RP)	37.1	36	0	1	4	4.10	1.10	17	32	9	7	32	4	1	0%
184	Max Kranick (RP) FA	37.0	25	0	1	5	3.65	1.05	15	34	5	5	24	3	2	0%
213	Daysbel Hernandez (ATL - RP)	37.0	33	0	2	10	3.41	1.54	14	27	30	3	39	4	3	0%
169	John Curtiss (ARI - RP) NRI	36.2	24	1	0	3	3.93	0.93	16	29	5	5	30	3	2	0%
191	Grant Taylor (CWS - RP)	36.2	54	6	1	9	4.66	1.39	19	36	15	0	36	2	4	8%
264	Kyle Harrison (MIL - SP,RP)	35.2	38	0	0	1	4.04	1.37	16	35	14	4	11	1	1	1%
280	Zack Kelly (BOS - SP,RP)	35.1	35	0	2	3	4.58	1.33	18	35	12	3	28	1	3	0%
195	Dylan Dodd (ATL - RP)	35.0	30	0	1	2	3.60	0.94	14	28	5	5	28	1	0	0%
279	Ryan Borucki (CWS - RP) NRI	35.0	32	0	3	7	4.63	1.29	18	29	16	4	39	1	3	0%
80	Felix Bautista (BAL - RP) IL60	34.2	50	19	1	0	2.60	1.13	10	16	23	3	35	1	1	2%
186	Chris Murphy (CWS - RP)	34.2	30	0	0	2	3.12	1.18	12	21	20	4	23	3	0	0%
225	Rico Garcia (BAL - RP)	34.1	38	0	0	10	3.15	1.19	12	31	10	5	29	0	2	0%
233	Jose Fermin (LAA - RP)	34.1	39	0	4	6	4.46	1.40	17	25	23	8	40	3	2	0%
199	Justin Slaten (BOS - RP)	34.0	25	3	3	7	4.24	1.09	16	27	10	3	36	2	4	0%
244	Nabil Crismatt (TEX - SP,RP) NRI	34.0	25	0	0	0	3.71	1.44	14	40	9	6	8	3	0	3%
228	Andrew Chafin (MIN - RP) NRI	33.2	36	0	0	4	2.41	1.43	9	29	19	2	42	1	1	0%
263	Yohan Ramirez (PIT - RP)	33.1	45	0	1	1	5.40	1.47	20	33	16	4	24	3	3	0%
127	AJ Blubaugh (HOU - SP,RP)	32.0	35	0	1	0	1.69	0.88	6	17	11	6	11	3	1	1%
162	Tommy Nance (TOR - RP)	31.2	32	0	0	5	1.99	1.01	7	25	7	0	30	2	0	0%
286	Brandon Waddell (NYM - RP) NRI	31.1	22	0	0	1	3.45	1.28	12	29	11	4	11	0	0	0%
179	Nic Enright (TOR - RP)	31.0	30	1	1	3	2.03	1.16	7	24	12	3	27	2	1	0%
193	Manuel Rodriguez (TB - RP) IL60	30.1	25	0	0	11	2.08	1.05	7	26	6	2	31	1	2	0%
187	Erik Miller (SF - RP)	30.0
"""


def parse_player(s):
    """Extract name and team from player string like 'Nick Martinez (TB - SP,RP)'."""
    s = s.strip()
    i = s.find('(')
    if i < 0:
        return s, ''
    name = s[:i].strip()
    rest = s[i+1:].rstrip(')').strip()
    # rest could be "TB - SP,RP" or "SP,RP" or "STL - RP"
    team = ''
    if ' - ' in rest:
        team = rest.split(' - ')[0].strip()
    return name, team


def norm_name(n):
    return n.strip().lower().replace('-', ' ').replace('.', '')


def main():
    base = Path(__file__).parent.parent
    with open(base / "public" / "data" / "pitchers.json") as f:
        data = json.load(f)
    existing = {norm_name(p["name"]) for p in data}

    rows = [r.strip() for r in USER_LIST.strip().split('\n') if r.strip()]
    def in_dataset(n):
        if n in existing:
            return True
        if n.replace('louis', 'louie').replace(' louie', ' louis') in existing:
            return True
        # "Daniel Lynch" matches "Daniel Lynch IV"
        parts = n.split()
        if len(parts) >= 2:
            base = ' '.join(parts[:2])
            for p in data:
                pn = norm_name(p["name"])
                if pn.startswith(base) or base in pn:
                    return True
        return False

    missing = []
    for row in rows:
        parts = row.split('\t')
        if len(parts) < 3:
            continue
        player_str = parts[1]
        name, team = parse_player(player_str)
        if not name:
            continue
        n = norm_name(name)
        if not in_dataset(n):
            missing.append((name, team, player_str))
    print("Missing from pitchers.json:")
    for name, team, raw in missing:
        print(f"  {name} ({team})")
    print(f"\nTotal missing: {len(missing)}")


if __name__ == "__main__":
    main()
