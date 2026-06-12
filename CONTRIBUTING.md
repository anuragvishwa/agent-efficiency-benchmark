# Contributing

Contributions should keep the benchmark reproducible without paid APIs,
managed services, model inference, Docker, or GPUs.

Before opening a change, run:

```bash
make validate
make signals
make benchmarks
make export
make test
make lint
```

Do not commit raw or processed Parquet files.
