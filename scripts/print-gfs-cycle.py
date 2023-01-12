from eht_met_forecast.gfs import latest_gfs_cycle_time

gfs = latest_gfs_cycle_time()

GFS_TIMESTAMP = '%Y%m%d_%H:00:00'
print(gfs.strftime(GFS_TIMESTAMP))
