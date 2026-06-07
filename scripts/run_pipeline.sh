#!/bin/bash

set -e

echo "Step 1. Upload local CSV files to HDFS"
bash scripts/upload_to_hdfs.sh

echo "Step 2. Create Hive external tables"
hive -f hive/create_tables.hql

echo "Step 3. Run Hive analysis queries"
hive -f hive/analysis_queries.hql

echo "Pipeline completed."
