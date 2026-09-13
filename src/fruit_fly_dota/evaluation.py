"""A disclosed bookkeeping rubric, not a validated biological measurement."""
def purity(manifest, memory="native", ablation="intact"):
    components = {
        "anatomical_connectivity_0_to_30": 30 if ablation == "intact" else 0,
        "physiology_0_to_20": 2,
        "anatomical_io_0_to_15": 0,
        "biological_learning_0_to_20": 0,
        "intrinsic_memory_0_to_10": 5 if memory == "native" else 0,
        "no_policy_bypass_0_to_5": 5,
    }
    return dict(score=sum(components.values()), out_of=100, rubric_version="0.1",
        components=components, selected_neurons=manifest["selected_neurons"],
        warning="Subjective accounting only; 100 is not a claim of consciousness or biological fidelity. Always report coverage and lesion controls.")
