-- RQ1. 30세 이상 타자의 나이 구간별 타구 질 변화
SELECT
    CASE
        WHEN age BETWEEN 30 AND 32 THEN '30-32'
        WHEN age BETWEEN 33 AND 35 THEN '33-35'
        WHEN age BETWEEN 36 AND 38 THEN '36-38'
        ELSE '39+'
    END AS age_group,
    COUNT(*) AS player_season_count,
    AVG(OPS) AS avg_ops,
    AVG(next_OPS) AS avg_next_ops,
    AVG(avg_launch_speed) AS avg_launch_speed,
    AVG(hard_hit_rate) AS avg_hard_hit_rate,
    AVG(avg_estimated_woba) AS avg_estimated_woba,
    AVG(avg_estimated_slg) AS avg_estimated_slg
FROM batter_final_model_data
GROUP BY
    CASE
        WHEN age BETWEEN 30 AND 32 THEN '30-32'
        WHEN age BETWEEN 33 AND 35 THEN '33-35'
        WHEN age BETWEEN 36 AND 38 THEN '36-38'
        ELSE '39+'
    END
ORDER BY age_group;

-- RQ2. 30세 이상 투수의 나이 구간별 구속/RPM 변화
SELECT
    CASE
        WHEN age BETWEEN 30 AND 32 THEN '30-32'
        WHEN age BETWEEN 33 AND 35 THEN '33-35'
        WHEN age BETWEEN 36 AND 38 THEN '36-38'
        ELSE '39+'
    END AS age_group,
    COUNT(*) AS player_season_count,
    AVG(WHIP) AS avg_whip,
    AVG(next_WHIP) AS avg_next_whip,
    AVG(ERA) AS avg_era,
    AVG(avg_release_speed) AS avg_release_speed,
    AVG(avg_effective_speed) AS avg_effective_speed,
    AVG(avg_release_spin_rate) AS avg_release_spin_rate,
    AVG(fastball_avg_speed) AS avg_fastball_speed,
    AVG(fastball_avg_spin) AS avg_fastball_spin,
    AVG(breaking1_avg_spin) AS avg_breaking1_spin
FROM pitcher_final_model_data
GROUP BY
    CASE
        WHEN age BETWEEN 30 AND 32 THEN '30-32'
        WHEN age BETWEEN 33 AND 35 THEN '33-35'
        WHEN age BETWEEN 36 AND 38 THEN '36-38'
        ELSE '39+'
    END
ORDER BY age_group;

-- RQ3. 직구/변화구 회전수와 다음 시즌 WHIP의 관계
SELECT
    CORR(fastball_avg_spin, next_WHIP) AS corr_fastball_spin_next_whip,
    CORR(breaking1_avg_spin, next_WHIP) AS corr_breaking1_spin_next_whip,
    CORR(avg_release_spin_rate, next_WHIP) AS corr_total_spin_next_whip,
    CORR(avg_release_speed, next_WHIP) AS corr_release_speed_next_whip
FROM pitcher_final_model_data
WHERE next_WHIP IS NOT NULL;

-- RQ4. Model A/B 성능 비교
SELECT
    dataset,
    target,
    feature_set,
    model_name,
    split_method,
    train_rows,
    test_rows,
    n_features,
    RMSE,
    MAE,
    R2
FROM model_performance_comparison
ORDER BY dataset, target, model_name, feature_set;

-- RQ5. 타자의 구속 구간별 타구 질 변화
SELECT
    velocity_bin_label,
    CASE
        WHEN statcast_age_bat_velocity BETWEEN 30 AND 32 THEN '30-32'
        WHEN statcast_age_bat_velocity BETWEEN 33 AND 35 THEN '33-35'
        WHEN statcast_age_bat_velocity BETWEEN 36 AND 38 THEN '36-38'
        ELSE '39+'
    END AS age_group,
    COUNT(*) AS row_count,
    SUM(velocity_pitch_count) AS total_pitch_count,
    SUM(velocity_batted_ball_count) AS total_batted_ball_count,
    AVG(avg_pitch_speed_in_bin) AS avg_pitch_speed_in_bin,
    AVG(velocity_avg_launch_speed) AS velocity_avg_launch_speed,
    AVG(velocity_hard_hit_rate) AS velocity_hard_hit_rate,
    AVG(velocity_avg_estimated_woba) AS velocity_avg_estimated_woba,
    AVG(velocity_avg_estimated_slg) AS velocity_avg_estimated_slg
FROM statcast_batter_velocity_bin_summary
GROUP BY
    velocity_bin_label,
    CASE
        WHEN statcast_age_bat_velocity BETWEEN 30 AND 32 THEN '30-32'
        WHEN statcast_age_bat_velocity BETWEEN 33 AND 35 THEN '33-35'
        WHEN statcast_age_bat_velocity BETWEEN 36 AND 38 THEN '36-38'
        ELSE '39+'
    END
ORDER BY velocity_bin_label, age_group;
