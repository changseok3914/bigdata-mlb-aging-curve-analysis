#!/bin/bash

set -e

echo "Create HDFS directories..."

hdfs dfs -mkdir -p /user/maria_dev/mlb/raw/statcast
hdfs dfs -mkdir -p /user/maria_dev/mlb/raw/lahman

hdfs dfs -rm -r -f /user/maria_dev/mlb/processed/batter_final_model_data
hdfs dfs -rm -r -f /user/maria_dev/mlb/processed/pitcher_final_model_data
hdfs dfs -rm -r -f /user/maria_dev/mlb/processed/statcast_batter_velocity_bin_summary
hdfs dfs -rm -r -f /user/maria_dev/mlb/results/tables/rq4_model_performance_comparison

hdfs dfs -mkdir -p /user/maria_dev/mlb/processed/batter_final_model_data
hdfs dfs -mkdir -p /user/maria_dev/mlb/processed/pitcher_final_model_data
hdfs dfs -mkdir -p /user/maria_dev/mlb/processed/statcast_batter_velocity_bin_summary
hdfs dfs -mkdir -p /user/maria_dev/mlb/results/tables/rq4_model_performance_comparison

echo "Upload raw data to HDFS..."

hdfs dfs -put -f data/raw/statcast/*.csv /user/maria_dev/mlb/raw/statcast/
hdfs dfs -put -f data/raw/lahman/*.csv /user/maria_dev/mlb/raw/lahman/

echo "Upload processed CSV files for Hive external tables..."

hdfs dfs -put -f data/processed/batter_final_model_data.csv /user/maria_dev/mlb/processed/batter_final_model_data/
hdfs dfs -put -f data/processed/pitcher_final_model_data.csv /user/maria_dev/mlb/processed/pitcher_final_model_data/
hdfs dfs -put -f data/processed/statcast_batter_velocity_bin_summary.csv /user/maria_dev/mlb/processed/statcast_batter_velocity_bin_summary/
hdfs dfs -put -f results/tables/rq4_model_performance_comparison.csv /user/maria_dev/mlb/results/tables/rq4_model_performance_comparison/

echo "Check HDFS uploaded files..."

hdfs dfs -du -h /user/maria_dev/mlb/raw/statcast | head
hdfs dfs -ls /user/maria_dev/mlb/processed
hdfs dfs -ls /user/maria_dev/mlb/results/tables

echo "HDFS upload completed."
