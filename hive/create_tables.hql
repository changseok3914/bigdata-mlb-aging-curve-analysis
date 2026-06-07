DROP TABLE IF EXISTS batter_final_model_data;
DROP TABLE IF EXISTS pitcher_final_model_data;
DROP TABLE IF EXISTS statcast_batter_velocity_bin_summary;
DROP TABLE IF EXISTS model_performance_comparison;

CREATE EXTERNAL TABLE batter_final_model_data (
    playerID STRING,
    nameFirst STRING,
    nameLast STRING,
    yearID INT,
    batted_ball_count INT,
    next_OPS DOUBLE,
    age INT,
    OPS DOUBLE,
    OBP DOUBLE,
    SLG DOUBLE,
    avg_launch_speed DOUBLE,
    avg_launch_angle DOUBLE,
    hard_hit_rate DOUBLE,
    avg_estimated_woba DOUBLE,
    avg_estimated_slg DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/maria_dev/mlb/processed/batter_final_model_data'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE pitcher_final_model_data (
    playerID STRING,
    nameFirst STRING,
    nameLast STRING,
    yearID INT,
    pitch_count INT,
    next_WHIP DOUBLE,
    age INT,
    WHIP DOUBLE,
    ERA DOUBLE,
    avg_release_speed DOUBLE,
    avg_effective_speed DOUBLE,
    avg_release_spin_rate DOUBLE,
    avg_release_extension DOUBLE,
    fastball_usage_rate DOUBLE,
    fastball_avg_speed DOUBLE,
    fastball_avg_effective_speed DOUBLE,
    fastball_avg_spin DOUBLE,
    fastball_avg_extension DOUBLE,
    breaking1_usage_rate DOUBLE,
    breaking1_avg_speed DOUBLE,
    breaking1_avg_effective_speed DOUBLE,
    breaking1_avg_spin DOUBLE,
    breaking1_avg_extension DOUBLE,
    breaking2_usage_rate DOUBLE,
    breaking2_avg_speed DOUBLE,
    breaking2_avg_effective_speed DOUBLE,
    breaking2_avg_spin DOUBLE,
    breaking2_avg_extension DOUBLE,
    has_breaking2 INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/maria_dev/mlb/processed/pitcher_final_model_data'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE statcast_batter_velocity_bin_summary (
    batter STRING,
    yearID INT,
    velocity_bin STRING,
    statcast_age_bat_velocity_sum DOUBLE,
    statcast_age_bat_velocity_count INT,
    velocity_pitch_count INT,
    release_speed_sum DOUBLE,
    release_speed_count INT,
    velocity_batted_ball_count INT,
    velocity_launch_speed_sum DOUBLE,
    velocity_launch_angle_sum DOUBLE,
    velocity_launch_angle_count INT,
    velocity_hard_hit_sum DOUBLE,
    velocity_xwoba_sum DOUBLE,
    velocity_xwoba_count INT,
    velocity_xslg_sum DOUBLE,
    velocity_xslg_count INT,
    velocity_bin_label STRING,
    statcast_age_bat_velocity DOUBLE,
    avg_pitch_speed_in_bin DOUBLE,
    velocity_avg_launch_speed DOUBLE,
    velocity_avg_launch_angle DOUBLE,
    velocity_hard_hit_rate DOUBLE,
    velocity_avg_estimated_woba DOUBLE,
    velocity_avg_estimated_slg DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/maria_dev/mlb/processed/statcast_batter_velocity_bin_summary'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE model_performance_comparison (
    dataset STRING,
    target STRING,
    feature_set STRING,
    model_name STRING,
    split_method STRING,
    train_rows INT,
    test_rows INT,
    n_features INT,
    RMSE DOUBLE,
    MAE DOUBLE,
    R2 DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/maria_dev/mlb/results/tables/rq4_model_performance_comparison'
TBLPROPERTIES ('skip.header.line.count'='1');
