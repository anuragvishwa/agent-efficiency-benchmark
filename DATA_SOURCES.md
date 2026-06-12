# Data Sources

## Terminal-Bench Trajectories

- Source: https://huggingface.co/datasets/yoonholee/terminalbench-trajectories
- License: Apache-2.0
- Current adapter: `src.ingestion.download_terminalbench`

The pipeline records dataset revision metadata in
`data/raw/terminalbench_source.json` when downloading. Raw and processed dataset
files are ignored by git.

## Future SWE-Agent Support

- Source: https://huggingface.co/datasets/nebius/SWE-agent-trajectories
- License: CC BY 4.0

This repository supports SWE-agent trajectories as a separate benchmark family.
Users must also respect licenses of represented repositories. The dataset card
also notes Llama 3.1 license obligations if using model outputs.
