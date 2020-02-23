#!/bin/bash

echo -n "Required Grafana version [ENTER]: "
read graf_ver
echo -n "Required Prometheus version [ENTER]: "
read prom_ver
echo -n "Required Prometheus retention to keep on disk [ENTER]: "
read prom_retention

sudo usermod -aG docker $(whoami)
git clone https://github.com/tuxiqae/monitoring_in_a_click.git
cd monitoring_in_a_click
pip3 install -r requirements.txt
python3 main.py --grafana-version "${graf_ver}" --prometheus-version "${prom_ver}" --retention "${prom_retention}"

