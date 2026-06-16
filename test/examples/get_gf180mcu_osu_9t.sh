#! /usr/bin/env bash

export GF180MCU_OSU_SC_COMMIT="8a2f58f283a2eaa725314c9e1b8b7d1d343f23a3"
export GF180MCU_FD_PR_COMMIT="4adc3a4704fbe722bdf2145341a409b6419788fd"
mkdir -p gf180mcu/spice
mkdir -p gf180mcu/models
curl -fsSL --retry 3 https://raw.githubusercontent.com/stineje/globalfoundries-pdk-libs-gf180mcu_osu_sc/$GF180MCU_OSU_SC_COMMIT/gf180mcu_osu_sc_gp9t3v3/spice/gf180mcu_osu_sc_gp9t3v3.spice > gf180mcu/spice/osu_sc_9t.spice
curl -fsSL --retry 3 https://raw.githubusercontent.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr/$GF180MCU_FD_PR_COMMIT/models/ngspice/design.spice > gf180mcu/models/design.spice
curl -fsSL --retry 3 https://raw.githubusercontent.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr/$GF180MCU_FD_PR_COMMIT/models/ngspice/sm141064.spice > gf180mcu/models/sm141064.spice
