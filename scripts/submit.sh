#!/bin/bash
#SBATCH --job-name=AME_Worker
#SBATCH --array=1-100
#SBATCH --time=00:10:00
#SBATCH --mem=2G
#SBATCH --output=logs/slurm_%A_%a.out

source ~/miniconda3/etc/profile.d/conda.sh
conda activate ame_env

# Remove the ../ from the python path
python src/worker.py $SLURM_ARRAY_TASK_ID