# Amplified Does Not Mean Predictive: Reasoning Behaviors in Thinking Models

**Jean de Dieu Nyandwi, Leena Mathur, Yonatan Bisk, Robert Hawkins, Graham Neubig**

[Paper](https://arxiv.org/abs/2608.13760) · [Website](https://neulab.github.io/behavioral-lift/) · [Dataset](https://huggingface.co/datasets/neulab/behavioral-lift)

We study a simple question:

> Do thinking models amplify the reasoning behaviors most associated with correct answers?

**Largely, no.** Thinking models produce more visible deliberation, but the behaviors they amplify most are not the behaviors most associated with correctness.

<p align="center">
  <img src="assets/amplification_mismatch.png" width="700"/>
</p>

The top-right quadrant is empty: no behavior is both strongly amplified in thinking models and strongly associated with correctness. Thinking models strongly amplify self-correction, hypothesis testing, and uncertainty acknowledgment. The highest-lift behaviors are different: confidence calibration, knowledge alignment, and self-awareness about missing information.

## Behavioral Lift

We introduce **Behavioral Lift**, a metric that separates how often a behavior appears from how much it is associated with correctness:

$$\text{Lift}(b) = P(\text{correct} \mid b) - P(\text{correct} \mid \neg b)$$

A behavior has high Lift when responses containing it are more often correct than responses without it. High prevalence alone is not enough: a behavior can appear frequently while adding little correctness signal. Behavioral Lift is a descriptive metric, not a causal estimate of what would happen if a behavior were forced into a trace.

<p align="center">
  <img src="assets/fig2_behavioral_lift.png" width="700"/>
</p>

Confidence calibration, knowledge alignment, and self-awareness have high positive Lift across modalities. Uncertainty acknowledgment is much weaker, and often negative, despite being strongly amplified in thinking traces.

## Key Takeaways

**Amplification is not Lift.** Thinking models reliably amplify correction, search, and uncertainty behaviors: self-correction, hypothesis testing, and uncertainty acknowledgment. The highest-lift behaviors are different: confidence calibration, knowledge alignment, and self-awareness about missing information.

**Calibration is not hedging.** Confidence calibration is one of the strongest positive signals of correctness across both LLMs and VLMs. Uncertainty acknowledgment is heavily amplified but weakly or negatively associated with correctness. A model that says "maybe" at every step is not calibrated. Calibration means confidence tracks the strength of the reasoning.

**Thinking models often win through recovery, not prevention.** Thinking models help most when tasks reward extended computation or recovery from intermediate mistakes. On tasks where fast recognition of the relevant pattern is enough, instruct models can perform comparably or better.

## Repository Structure

```text
prompts/        Annotation prompts for LLM and VLM traces
taxonomy/      Behavior definitions, failure modes, and JSON schemas
metrics/       Minimal code for Behavioral Lift and Recovery Rate
examples/      Small LLM/VLM sample annotation files
assets/        README figures
```

Model responses were collected using [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) for LLMs and [lmms-eval](https://github.com/EvolvingLMMs-Lab/lmms-eval) for VLMs under standardized chain-of-thought evaluation settings.

The full annotation dataset is available on Hugging Face: [neulab/behavioral-lift](https://huggingface.co/datasets/neulab/behavioral-lift)

```python
from datasets import load_dataset

ds = load_dataset("neulab/behavioral-lift")
llm = ds["llm"]   # 8,282 rows
vlm = ds["vlm"]   # 7,000 rows
```

## Running The Metric Scripts

Compute Behavioral Lift on the sample LLM annotations:

```bash
python3 metrics/behavioral_lift.py \
  examples/sample_llm_annotations.jsonl \
  --output results/sample_llm_behavioral_lift.csv
```

Compute Recovery Rate on the sample LLM annotations:

```bash
python3 metrics/recovery_rate.py \
  examples/sample_llm_annotations.jsonl \
  --output results/sample_llm_recovery_rate.csv
```

Run the same metrics on the VLM sample annotations:

```bash
python3 metrics/behavioral_lift.py \
  examples/sample_vlm_annotations.jsonl \
  --output results/sample_vlm_behavioral_lift.csv

python3 metrics/recovery_rate.py \
  examples/sample_vlm_annotations.jsonl \
  --output results/sample_vlm_recovery_rate.csv
```

You can group results by metadata fields such as `model`, `benchmark`, or `modality`:

```bash
python3 metrics/behavioral_lift.py \
  examples/sample_llm_annotations.jsonl \
  --output results/sample_llm_behavioral_lift_by_model.csv \
  --group-by model benchmark

python3 metrics/recovery_rate.py \
  examples/sample_vlm_annotations.jsonl \
  --output results/sample_vlm_recovery_by_model.csv \
  --group-by model benchmark
```

The metric scripts accept either a single JSONL file or a directory containing JSONL files.

## Citation

```bibtex
@article{nyandwi2026amplified,
  title={Amplified Does Not Mean Predictive: Reasoning Behaviors in Thinking Models},
  author={Nyandwi, Jean de Dieu and Mathur, Leena and Bisk, Yonatan and Hawkins, Robert and Neubig, Graham},
  journal={arXiv preprint arXiv:2608.13760},
  year={2026}
}
```