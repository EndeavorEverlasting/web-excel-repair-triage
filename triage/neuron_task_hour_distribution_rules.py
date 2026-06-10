"""Neuron task-hour distribution rules.

The roster proves who worked and when, but it usually does not prove the exact
intra-day Neuron task mix. These rules make the generator choose conservative,
repeatable task lanes when event-level evidence is thin.

Important posture: ordinary 9-to-6 Neuron work is support by default, not field
deployment by default. Deployment classification requires