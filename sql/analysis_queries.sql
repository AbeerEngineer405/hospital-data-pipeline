
-- Query 1: Appointment status distribution
SELECT
    status,
    COUNT(*) AS total_appointments
FROM appointments
GROUP BY status
ORDER BY total_appointments DESC;


-- Query 2: Claim financial summary by status
SELECT
    claim_status,
    COUNT(*) AS total_claims,
    ROUND(SUM(amount), 2) AS total_amount,
    ROUND(AVG(amount), 2) AS average_amount
FROM claims
GROUP BY claim_status
ORDER BY total_amount DESC;


-- Query 3: Claims linked to appointment statuses
SELECT
    a.status AS appointment_status,
    COUNT(c.claim_id) AS total_claims,
    ROUND(SUM(c.amount), 2) AS total_claim_amount
FROM appointments AS a
INNER JOIN claims AS c
    ON a.appointment_id = c.appointment_id
GROUP BY a.status
ORDER BY total_claim_amount DESC;


-- Query 4: Support interaction analysis
SELECT
    issue_type,
    resolution_status,
    COUNT(*) AS total_interactions
FROM support
GROUP BY
    issue_type,
    resolution_status
ORDER BY
    issue_type,
    total_interactions DESC;


-- Query 5: Operational KPI - Appointment completion rate
SELECT
    COUNT(*) AS total_appointments,
    SUM(
        CASE
            WHEN status = 'Completed' THEN 1
            ELSE 0
        END
    ) AS completed_appointments,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN status = 'Completed' THEN 1
                ELSE 0
            END
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS completion_rate_percent
FROM appointments;


-- Query 6: Data quality investigation - Claim relationship issues
SELECT
    c.claim_id,
    c.appointment_id,
    c.patient_id AS claim_patient_id,
    a.patient_id AS appointment_patient_id,
    CASE
        WHEN a.appointment_id IS NULL
            THEN 'Missing appointment'
        WHEN c.patient_id <> a.patient_id
            THEN 'Patient mismatch'
        ELSE 'Valid'
    END AS quality_issue
FROM claims AS c
LEFT JOIN appointments AS a
    ON c.appointment_id = a.appointment_id
WHERE
    a.appointment_id IS NULL
    OR c.patient_id <> a.patient_id;


-- Query 7: Top 10 patients by appointment count
SELECT
    p.patient_id,
    COUNT(a.appointment_id) AS total_appointments
FROM patients AS p
LEFT JOIN appointments AS a
    ON p.patient_id = a.patient_id
GROUP BY p.patient_id
ORDER BY total_appointments DESC, p.patient_id
LIMIT 10;
