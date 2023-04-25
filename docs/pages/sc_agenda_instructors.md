# Course Agenda

## May 2: Introduction/Theory/Software
- Overview and Welcome (5 min, KL)
- Basic Theory incl Reflection Zones (45 min, FN) 
- Break (10 min)
- How to Run the Code, Questions (60 min, KL) 
  - big picture, how to find our codebase and answer your own questions
  - main modules : rinex2snr, quickLook, gnssir
  - how to compute reflection zones (5 min)
  - brief outline of products: vwc, snowdepth, subdaily
  - if have time, could show the API, but right now it is on Day 4

- Questions (5 min)

## May 3: Hydrologic Applications
- Short Intro on Snow and Ice (10 min, KL)
- Ice sheet example (10-15 min, KE) 
  - Antarctica (LTHW)
  - Greenland  (GLS1, if time)
- Snow accumulation examples (20 min, KL)
  - P041
  - P101
- Break (10 minutes)
- Soil Moisture (40 min, KL) 
  - PBO H2O approach (20 min)
  - P038 (10 min)
  - MCHL (10 min)
- Questions (5 min)

## May 4: Water Applications
- Short Intro (5 min, KL) 
- Background on models needed/used for water monitoring (35, SW)
- make sure to tell them to use daily_avg for lakes and usually rivers
subdaily is for tides.  uses a spline etc
- Lake example using daily_avg (10 min, KE)
  - TGHO
- Break (10 minutes)
- Using subdaily
  - Tide example (10 min, SC02 SW)
  - Tide example (10 min, AC12 SW)
  - Tide example (10 min, TGGO SW)
- invsnr method (15 min, DP) 
make sure they understand the differences from the LSP approach.
LSP used as starting solution, smooth assumption.

- Questions (5 min)

## May 5: Going Forward
- Short Intro (5 min, KL)
- https://gnss-reflections.org API (10 min, KL)
- Why is it so hard to find good GNSS data? (10 min, KL)
- How to make a good installation (10-15 min, TN) 
  - in particular, the issues you faced when you picked new sites in Greenland
  - how tall, receiver sampling rates, which frequenciesS? which receiver and antenna to buy? which side of the building, avoiding ships as much as you can.  

- Break (10 minutes)

- How to report bugs, ask questions (10 min, TD)
- Improvements (20 min, TD)  
  - Better refraction (in progress)
  - SWH calculation and **correction**
  - surface slopes
  - ITRF
  - Equipment database
  - Community: Adv models for SWE and soil moisture
- Low-cost sensors: (10-15 min, SW)
- Questions: remainder of the time

