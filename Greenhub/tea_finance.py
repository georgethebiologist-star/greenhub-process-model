"""Pure screening-finance calculations for post-route GreenHub TEA.

The functions here never inspect or alter a process model.  They consume only
annual TEA totals and explicit financial assumptions prepared after simulation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Mapping, Sequence


@dataclass(frozen=True)
class TEAProductPrice:
    """A traceable user or source supplied sale-price assumption."""

    product_id: str
    value_eur_per_unit: float
    unit: str
    source_status: str = "user_input"
    source_title: str = ""
    source_url: str = ""
    notes: str = ""
    basis: str = "as-sold product; no dry-matter conversion inferred"
    geography: str = "unspecified"
    reference_year: int | None = None
    reference_period: str = ""
    source_table_or_page: str = ""
    retrieval_date: str | None = None
    evidence_class: str = "explicit_user_assumption"
    applicability: str = "Unverified product quality; screening only."
    conversion_method: str = "none"
    uncertainty: str = "unquantified"
    quality_basis: str = "screening_assumption"
    quality_requirements: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.product_id:
            raise ValueError("A product price requires product_id.")
        if not isfinite(float(self.value_eur_per_unit)) or self.value_eur_per_unit < 0:
            raise ValueError("Product prices must be finite and non-negative.")
        if _price_basis(self.unit) is None:
            raise ValueError(
                "Product price unit must be EUR/kg, EUR/t, EUR/m3, or EUR/Nm3."
            )
        if not self.source_status:
            raise ValueError("A product price requires source_status for traceability.")
        if self.quality_basis not in {"screening_assumption", "matched_specification"}:
            raise ValueError("quality_basis must be screening_assumption or matched_specification.")
        if self.quality_basis == "matched_specification" and not self.quality_requirements:
            raise ValueError("matched_specification requires quality_requirements.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TEAFinancialAssumptions:
    """Explicit screening assumptions; omitted investment inputs stay blocked."""

    project_lifetime_years: int | None = None
    discount_rate: float | None = None
    capex_spend_fractions: tuple[float, ...] = (1.0,)
    tax_rate: float = 0.0
    depreciation_method: str = "none"
    depreciation_years: int | None = None
    working_capital_eur: float = 0.0
    working_capital_recovery_fraction: float = 1.0
    residual_value_eur: float = 0.0
    product_prices: Mapping[str, object] = field(default_factory=dict)
    revenue_product_ids: tuple[str, ...] = ()
    non_sale_product_reasons: Mapping[str, str] = field(default_factory=dict)
    replacement_years_by_cost_id: Mapping[str, tuple[int, ...]] = field(default_factory=dict)
    replacement_cost_fraction_by_cost_id: Mapping[str, float] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        if self.project_lifetime_years is not None and (
            type(self.project_lifetime_years) is not int or not 1 <= self.project_lifetime_years <= 200
        ):
            raise ValueError("project_lifetime_years must be an integer within [1, 200] or null.")
        if self.discount_rate is not None and (
            not isfinite(float(self.discount_rate)) or self.discount_rate <= -1
        ):
            raise ValueError("discount_rate must be finite and greater than -1, or null.")
        if not 0 <= self.tax_rate <= 1:
            raise ValueError("tax_rate must be within [0, 1].")
        if self.depreciation_method not in {"none", "straight_line"}:
            raise ValueError("depreciation_method must be 'none' or 'straight_line'.")
        if self.depreciation_method == "straight_line" and (
            type(self.depreciation_years) is not int or self.depreciation_years <= 0
        ):
            raise ValueError("straight_line depreciation requires positive depreciation_years.")
        if not self.capex_spend_fractions or any(
            not isfinite(float(value)) or value < 0 for value in self.capex_spend_fractions
        ):
            raise ValueError("capex_spend_fractions must contain finite non-negative values.")
        if abs(sum(self.capex_spend_fractions) - 1.0) > 1e-9:
            raise ValueError("capex_spend_fractions must sum to 1.0.")
        for name, value in (
            ("working_capital_eur", self.working_capital_eur),
            ("residual_value_eur", self.residual_value_eur),
        ):
            if not isfinite(float(value)) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative.")
        if not 0 <= self.working_capital_recovery_fraction <= 1:
            raise ValueError("working_capital_recovery_fraction must be within [0, 1].")
        for cost_id, years in self.replacement_years_by_cost_id.items():
            if any(type(year) is not int or year <= 0 for year in years):
                raise ValueError(f"Replacement years for {cost_id} must be positive integers.")
        for cost_id, fraction in self.replacement_cost_fraction_by_cost_id.items():
            if not isfinite(float(fraction)) or fraction < 0:
                raise ValueError(f"Replacement fraction for {cost_id} must be non-negative.")
        normalize_product_prices(self.product_prices)
        if any(not isinstance(reason, str) or not reason.strip() for reason in self.non_sale_product_reasons.values()):
            raise ValueError("Every non-sale product requires an explicit disposition reason.")

    @property
    def construction_years(self) -> int:
        return len(self.capex_spend_fractions)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["construction_years"] = self.construction_years
        payload["product_prices"] = {
            item.product_id: item.to_dict() for item in normalize_product_prices(self.product_prices)
        }
        return payload


def normalize_product_prices(values: Mapping[str, object]) -> tuple[TEAProductPrice, ...]:
    prices: list[TEAProductPrice] = []
    for product_id, raw in values.items():
        if isinstance(raw, TEAProductPrice):
            price = raw
            if price.product_id != product_id:
                raise ValueError(
                    f"Product-price key '{product_id}' does not match '{price.product_id}'."
                )
        elif isinstance(raw, Mapping):
            data = dict(raw)
            value = data.pop("value_eur_per_unit", data.pop("value", None))
            if value is None:
                raise ValueError(f"Product price '{product_id}' requires a value.")
            price = TEAProductPrice(
                product_id=str(product_id), value_eur_per_unit=float(value), **data
            )
        else:
            raise TypeError(
                f"Product price '{product_id}' must be TEAProductPrice or a mapping."
            )
        prices.append(price)
    return tuple(prices)


def calculate_screening_financials(
    *,
    installed_capex_eur: float | None,
    annual_opex_eur: float,
    annual_revenue_eur: float,
    annual_feed_kg: float | None,
    annual_protein_product_kg: float | None,
    annual_biomethane_nm3: float | None,
    assumptions: TEAFinancialAssumptions,
    replacement_events: Sequence[Mapping[str, object]] = (),
    capex_complete: bool,
    opex_complete: bool,
    revenue_complete: bool,
) -> tuple[dict[str, object], tuple[dict[str, object], ...], tuple[str, ...]]:
    """Return deterministic cash-flow KPIs without filling missing finance inputs."""

    gross_profit = annual_revenue_eur - annual_opex_eur
    profit_complete = opex_complete and revenue_complete
    kpis: dict[str, object] = {
        "annual_gross_profit_eur": gross_profit if profit_complete else None,
        "net_operating_margin_eur_per_year": gross_profit if profit_complete else None,
        "ebitda_like_operating_cash_flow_eur_per_year": gross_profit if profit_complete else None,
        "partial_operating_margin_eur_per_year": gross_profit,
        "profit_status": "complete_screening" if profit_complete else "incomplete",
        "profit_definition": "Annual product revenue minus annual operating expenditure before depreciation, tax and financing; replacement CAPEX is in cash flows only.",
        "npv_eur": None,
        "irr": None,
        "simple_payback_years": None,
        "discounted_payback_years": None,
        "cost_per_tonne_wet_feed_eur": _divide(annual_opex_eur, _tonnes(annual_feed_kg)),
        "cost_per_kg_protein_product_eur": _divide(
            annual_opex_eur, annual_protein_product_kg
        ),
        "cost_per_nm3_biomethane_eur": _divide(
            annual_opex_eur, annual_biomethane_nm3
        ),
        "cost_intensity_status": "complete" if opex_complete else "partial_opex",
        "financial_kpi_status": "blocked_missing_financial_inputs",
    }
    warnings: list[str] = []
    blockers: list[str] = []
    if not capex_complete or installed_capex_eur is None:
        blockers.append("incomplete_installed_capex")
    if not opex_complete:
        blockers.append("incomplete_annual_opex")
    if not revenue_complete:
        blockers.append("incomplete_product_revenue")
    if assumptions.project_lifetime_years is None:
        blockers.append("missing_project_lifetime")
    if assumptions.discount_rate is None:
        blockers.append("missing_discount_rate")
    if blockers:
        kpis["financial_kpi_blockers"] = blockers
        warnings.append(
            "Investment-return KPIs were not calculated because required CAPEX, OPEX, "
            "revenue, lifetime, or discount-rate inputs are incomplete."
        )
        return kpis, (), tuple(warnings)

    capex = float(installed_capex_eur)
    lifetime = int(assumptions.project_lifetime_years)
    discount_rate = float(assumptions.discount_rate)
    construction_years = assumptions.construction_years
    cashflows: list[dict[str, object]] = []
    replacement_by_year: dict[int, float] = {}
    replacement_ids_by_year: dict[int, list[str]] = {}
    for event in replacement_events:
        year = int(event["year"])
        if 1 <= year <= lifetime:
            replacement_by_year[year] = replacement_by_year.get(year, 0.0) + float(
                event["replacement_capex_eur"]
            )
            replacement_ids_by_year.setdefault(year, []).append(str(event["cost_id"]))

    for year, fraction in enumerate(assumptions.capex_spend_fractions):
        cashflows.append(
            {
                "year": year,
                "phase": "construction",
                "revenue_eur": 0.0,
                "opex_eur": 0.0,
                "ebitda_like_eur": 0.0,
                "depreciation_eur": 0.0,
                "tax_eur": 0.0,
                "initial_capex_eur": capex * float(fraction),
                "replacement_capex_eur": 0.0,
                "working_capital_change_eur": -assumptions.working_capital_eur if year == 0 else 0.0,
                "residual_value_eur": 0.0,
                "net_cash_flow_eur": -capex * float(fraction)
                - (assumptions.working_capital_eur if year == 0 else 0.0),
                "replacement_cost_ids": [],
            }
        )

    annual_depreciation = 0.0
    if assumptions.depreciation_method == "straight_line":
        annual_depreciation = capex / int(assumptions.depreciation_years)
    for operating_year in range(1, lifetime + 1):
        year = construction_years - 1 + operating_year
        depreciation = (
            annual_depreciation
            if assumptions.depreciation_method == "straight_line"
            and operating_year <= int(assumptions.depreciation_years)
            else 0.0
        )
        taxable_income = max(0.0, gross_profit - depreciation)
        tax = taxable_income * assumptions.tax_rate
        replacement = replacement_by_year.get(operating_year, 0.0)
        residual = assumptions.residual_value_eur if operating_year == lifetime else 0.0
        working_capital_recovery = (
            assumptions.working_capital_eur * assumptions.working_capital_recovery_fraction
            if operating_year == lifetime
            else 0.0
        )
        cashflows.append(
            {
                "year": year,
                "phase": "operation",
                "operating_year": operating_year,
                "revenue_eur": annual_revenue_eur,
                "opex_eur": annual_opex_eur,
                "ebitda_like_eur": gross_profit,
                "depreciation_eur": depreciation,
                "tax_eur": tax,
                "initial_capex_eur": 0.0,
                "replacement_capex_eur": replacement,
                "working_capital_change_eur": working_capital_recovery,
                "residual_value_eur": residual,
                "net_cash_flow_eur": gross_profit - tax - replacement + residual
                + working_capital_recovery,
                "replacement_cost_ids": replacement_ids_by_year.get(operating_year, []),
            }
        )

    values = [float(row["net_cash_flow_eur"]) for row in cashflows]
    try:
        discounted_values = [value / (1.0 + discount_rate) ** year for year, value in enumerate(values)]
        npv = sum(discounted_values)
        if not all(isfinite(value) for value in discounted_values) or not isfinite(npv):
            raise OverflowError
    except (OverflowError, ZeroDivisionError):
        kpis.update(financial_kpi_status="blocked_numeric_financial_range", financial_kpi_blockers=["discount_rate_and_lifetime_exceed_numeric_range"])
        warnings.append("Discount-rate/lifetime combination exceeds finite numeric range; investment KPIs withheld. Supply a numerically meaningful financial basis.")
        return kpis, tuple(cashflows), tuple(warnings)
    kpis.update(
        npv_eur=npv,
        irr=_irr(values),
        simple_payback_years=_payback(values, 0.0),
        discounted_payback_years=_payback(values, discount_rate),
        financial_kpi_status="calculated_screening",
        financial_kpi_blockers=[],
    )
    if assumptions.depreciation_method == "none" and assumptions.tax_rate > 0:
        warnings.append(
            "Tax is calculated without depreciation because depreciation_method='none'."
        )
    if _sign_changes(values) > 1:
        warnings.append("IRR withheld: cash flows have multiple sign changes, so a unique economically meaningful IRR is not guaranteed.")
    warnings.append("Cash flows are unlevered and in constant project-year EUR: no debt, inflation, escalation, loss carry-forward or replacement depreciation is inferred.")
    if annual_protein_product_kg and annual_biomethane_nm3:
        warnings.append(
            "Product-specific costs divide total annual OPEX by one product at a time; "
            "no multi-product cost allocation has been applied."
        )
    return kpis, tuple(cashflows), tuple(warnings)


def _irr(cashflows: Sequence[float]) -> float | None:
    if not cashflows or not any(value < 0 for value in cashflows) or not any(
        value > 0 for value in cashflows
    ) or _sign_changes(cashflows) != 1:
        return None
    low, high = -0.999999, 1.0

    def value(rate: float) -> float:
        # Horner evaluation avoids underflow of (1+r)**year at long lifetimes.
        inverse = 1.0 / (1.0 + rate)
        total = 0.0
        for flow in reversed(cashflows):
            total = flow + total * inverse
        return total

    low_value, high_value = value(low), value(high)
    while low_value * high_value > 0 and high < 1_000_000:
        high *= 2.0
        high_value = value(high)
    if low_value * high_value > 0:
        return None
    for _ in range(200):
        mid = (low + high) / 2.0
        mid_value = value(mid)
        if abs(mid_value) < 1e-8:
            return mid
        if low_value * mid_value <= 0:
            high = mid
        else:
            low, low_value = mid, mid_value
    return (low + high) / 2.0


def _sign_changes(values: Sequence[float]) -> int:
    signs = [value > 0 for value in values if value != 0]
    return sum(left != right for left, right in zip(signs, signs[1:]))


def _payback(cashflows: Sequence[float], discount_rate: float) -> float | None:
    cumulative = 0.0
    for year, flow in enumerate(cashflows):
        discounted = flow / (1.0 + discount_rate) ** year
        previous = cumulative
        cumulative += discounted
        if cumulative >= 0 and year > 0:
            positive_increment = cumulative - previous
            fraction = (-previous / positive_increment) if positive_increment > 0 else 0.0
            return (year - 1) + fraction
    return None


def _tonnes(value_kg: float | None) -> float | None:
    return None if value_kg is None else value_kg / 1000.0


def _divide(numerator: float, denominator: float | None) -> float | None:
    return None if denominator is None or denominator <= 0 else numerator / denominator


def _price_basis(unit: str) -> str | None:
    normalized = unit.strip().lower().replace(" ", "")
    if normalized in {"eur/kg", "€/kg"}:
        return "kg"
    if normalized in {"eur/t", "eur/tonne", "€/t", "€/tonne"}:
        return "tonne"
    if normalized in {"eur/m3", "eur/nm3", "€/m3", "€/nm3"}:
        return "m3"
    return None


__all__ = (
    "TEAFinancialAssumptions",
    "TEAProductPrice",
    "calculate_screening_financials",
    "normalize_product_prices",
)
