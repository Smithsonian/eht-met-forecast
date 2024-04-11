export SLACK_QUIET=1

# pre-2024
#export STATIONS="Aa Ax BAJA BOL BRZ CAT CNI GAM Gl GLTS HAY Kt LAS Lm Mg Mm Nn OVRO PIKES Pv Sw Sz VLA VLT KVN-Pyeonchang"
# 2024
export STATIONS="Aa Ax BAJA CNI GAM Gl GLTS HAY JELM Kt LAS LLA Lm Mg Mm Nn OVRO Pv Sw Sz KVN-Pyeongchang Ky"

export START="0 days"
export END="14 days"
export VEX=
#export VEX="--vex 2024/*.vex"
export EMPHASIZE="Nn:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm:Pv:Ky"

# this is where we put the downloaded data, it is only checked in if complete 210 lines
export DEST=~/github/eht-met-data

# this data directory should be the checked in data, with no partial files
export DATA=~/github/eht-met-data-prod

# eht-work -- NFS mounts homedirs from eht-filer
export UPLOAD=glindahl@35.199.60.65
