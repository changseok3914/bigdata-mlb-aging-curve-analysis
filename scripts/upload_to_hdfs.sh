#!/bin/bash

set -e

echo "Create HDFS directories..."

hdfs dfs -mkdir -p /user/mlb/raw/statcast
hdfs dfs -mkdir -p /user/mlb/raw/lahman

hdfs dfs -rm -r -f /user/mlb/processed/batter_final_model_data
hdfs dfs -rm -r -f /user/mlb/processed/pitcher_final_model_data
hdfs dfs -rm -r -f /user/mlb/processed/statcast_batter_velocity_bin_summary
hdfs dfs -rm -r -f /user/mlb/results/tables/rq4_model_performance_comparison

hdfs dfs -mkdir -p /user/mlb/processed/batter_final_model_data
hdfs dfs -mkdir -p /user/mlb/processed/pitcher_final_model_data
hdfs dfs -mkdir -p /user/mlb/processed/statcast_batter_velocity_bin_summary
hdfs dfs -mkdir -p /user/mlb/results/tables/rq4_model_performance_comparison

echo "Upload raw data to HDFS..."

hdfs dfs -put -f data/raw/statcast/*.csv /user/mlb/raw/statcast/
hdfs dfs -put -f data/raw/lahman/*.csv /user/mlb/raw/lahman/

echo "Upload processed CSV files for Hive external tables..."

hdfs dfs -put -f data/processed/batter_final_model_data.csv /user/mlb/processed/batter_final_model_data/
hdfs dfs -put -f data/processed/pitcher_final_model_data.csv /user/mlb/processed/pitcher_final_model_data/
hdfs dfs -put -f data/processed/statcast_batter_velocity_bin_summary.csv /user/mlb/processed/statcast_batter_velocity_bin_summary/
hdfs dfs -put -f results/tables/rq4_model_performance_comparison.csv /user/mlb/results/tables/rq4_model_performance_comparison/

echo "Check HDFS uploaded files..."

hdfs dfs -du -h /user/mlb/raw/statcast | head
hdfs dfs -ls /user/mlb/processed
hdfs dfs -ls /user/mlb/results/tables

echo "HDFS upload completed."
