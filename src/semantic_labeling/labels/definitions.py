from __future__ import annotations


# This is the shared label catalog.
# The IDs are placeholders for now, but this keeps the label identity stable
# even if we reuse the same labels for other questions later.

LABEL_DEFINITIONS = {
    "TRIG_SUBSTITUTION": {"label_id": "MAT0001", "name": "TRIG_SUBSTITUTION"},
    "POWER_OF_A_PRODUCT": {"label_id": "MAT0002", "name": "POWER_OF_A_PRODUCT"},
    "TRIG_IDENTITY": {"label_id": "MAT0003", "name": "TRIG_IDENTITY"},
    "FRACTIONAL_EXPONENT_TO_ROOT": {"label_id": "MAT0004", "name": "FRACTIONAL_EXPONENT_TO_ROOT"},
    "RADICAL_REWRITE": {"label_id": "MAT0005", "name": "RADICAL_REWRITE"},
    "CONSTANT_SUBSTITUTION": {"label_id": "MAT0006", "name": "CONSTANT_SUBSTITUTION"},
    "FACTORING": {"label_id": "MAT0007", "name": "FACTORING"},
    "ROOT_PRODUCT_RULE": {"label_id": "MAT0008", "name": "ROOT_PRODUCT_RULE"},
    "SQRT_TO_ABS": {"label_id": "MAT0009", "name": "SQRT_TO_ABS"},
    "TRIG_SQUARE_REWRITE": {"label_id": "MAT0010", "name": "TRIG_SQUARE_REWRITE"},
    "DIFFERENTIATION": {"label_id": "MAT0011", "name": "DIFFERENTIATION"},
    "DIFFERENTIAL_REWRITE": {"label_id": "MAT0012", "name": "DIFFERENTIAL_REWRITE"},
    "INTEGRAND_SUBSTITUTION": {"label_id": "MAT0013", "name": "INTEGRAND_SUBSTITUTION"},
    "CANCEL_COMMON_FACTOR": {"label_id": "MAT0014", "name": "CANCEL_COMMON_FACTOR"},
    "TRIG_RATIO_REWRITE": {"label_id": "MAT0015", "name": "TRIG_RATIO_REWRITE"},
    "INTEGRAL_SPLIT": {"label_id": "MAT0016", "name": "INTEGRAL_SPLIT"},
    "ANTIDERIVATIVE": {"label_id": "MAT0017", "name": "ANTIDERIVATIVE"},
    "BACK_SUBSTITUTION": {"label_id": "MAT0018", "name": "BACK_SUBSTITUTION"},
    "REFERENCE_TRIANGLE": {"label_id": "MAT0019", "name": "REFERENCE_TRIANGLE"},
}


def make_label(name: str) -> dict[str, str]:
    return dict(LABEL_DEFINITIONS[name])
