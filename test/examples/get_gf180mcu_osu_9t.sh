#! /usr/bin/env bash

mkdir -p gf180mcu/spice
mkdir -p gf180mcu/models
curl -s https://raw.githubusercontent.com/stineje/globalfoundries-pdk-libs-gf180mcu_osu_sc/refs/heads/main/gf180mcu_osu_sc_gp9t3v3/spice/gf180mcu_osu_sc_gp9t3v3.spice > gf180mcu/spice/osu_sc_9t.spice
curl -s https://raw.githubusercontent.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr/refs/heads/main/models/ngspice/design.spice > gf180mcu/models/design.spice
curl -s https://raw.githubusercontent.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr/refs/heads/main/models/ngspice/sm141064.spice > gf180mcu/models/sm141064.spice
