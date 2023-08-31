#!/usr/bin/env bash

pip install earthscope-cli
es sso login

es sso access --token > sso_token.json

cp sso_token.json "../notebooks/"

#echo running learn-the-code notebooks pass/fail
#pytest --nbmake --nbmake-timeout=3000 -n=auto "../notebooks/learn-the-code"

echo testing ice sheet cases:
pytest --nbmake --nbmake-timeout=3000 -n=auto "../notebooks/use-cases/Ice_Sheets"

echo testing lakes and river cases:
pytest --nbmake --nbmake-timeout=3000 -n=auto  "../notebooks/use-cases/Lakes_and_Rivers"

echo testing snow accumulation cases:
pytest --nbmake --nbmake-timeout=3000 -n=auto "../notebooks/use-cases/Seasonal_Snow_Accumulation"

echo testing soil moisture cases
pytest --nbmake --nbmake-timeout=3000 -n=auto "../notebooks/use-cases/Soil_Moisture"

echo testing tides cases
pytest --nbmake --nbmake-timeout=3000 -n=auto "../notebooks/use-cases/Tides"

