#!/bin/bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate ame_env

rm -rf data_phase1 data_phase2
mkdir -p data

echo "Starting Wake Phase 1..."
JOB_ID=$(sbatch --parsable scripts/submit.sh)
echo "Submitted Phase 1 (Job ID: $JOB_ID). Waiting for completion..."

while squeue -h -j $JOB_ID | grep -q .; do
    sleep 5
done
echo "Phase 1 complete."

mv data data_phase1
mkdir -p data

echo "Running Aggregator..."
python src/aggregator.py

echo "Starting Wake Phase 2..."
JOB_ID=$(sbatch --parsable scripts/submit.sh)
echo "Submitted Phase 2 (Job ID: $JOB_ID). Waiting for completion..."

while squeue -h -j $JOB_ID | grep -q .; do
    sleep 5
done
echo "Phase 2 complete."

mv data data_phase2
mkdir -p data

echo "Running Analysis..."
python src/analyze.py