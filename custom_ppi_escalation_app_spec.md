# Custom PPI escalation index: result-view app specification

**Functional, Interaction, and Data Contract Specification**

> Project status (2026-11-03): post-MVP, not implemented, and blocked on M3.
> Proposed FastMCP components, dependencies, and open compatibility items
> are in [docs/component_list.md](docs/component_list.md).

| **Document item**          | **Value**                                          |
|----------------------------|----------------------------------------------------|
| **Version**                | 0.1                                                |
| **Status**                 | Draft for implementation                           |
| **Date**                   | 2026-10-30                                         |
| **Implementation context** | FastMCP App with a Prefab-based presentation layer |

> **Core convention:** the annual base-year index factor is 1.0. The selected-component detail view displays that factor as 100%.

**Scope**

> Allocation ribbon, weighted stacked-area index view, component detail, year-to-base adjustment waterfall, auditable table, and CSV export.

# 1. Purpose

This specification defines the result-view experience for a custom escalation index built from multiple Producer Price Index (PPI) series. Each component PPI is normalized to the same base year, each component is assigned a fixed allocation weight, the allocation weights sum to 1, and the weighted components form a composite escalation index.

The app must let a user:

- understand the allocation basis and the PPI series included in the basket;

- see how the weighted component levels combine into the custom index over time;

- select one PPI and inspect its unweighted normalized or raw history;

- optionally calculate and explain the adjustment from a selected year to the base year;

- inspect the underlying data in a table; and

- export the table as a deterministic CSV file.

This document defines the user interface, calculation semantics, return-data format, and acceptance criteria. It does not define BLS download, ingestion, basket design, or source-series selection workflows.

# 2. Product goals

The result view shall:

> 1\. Make the basket composition immediately visible.
>
> 2\. Preserve the identity and assigned color of each PPI across all visual elements.
>
> 3\. Show the composite index as the exact sum of weighted normalized component levels.
>
> 4\. Keep normalized, raw, weighted, and composite quantities clearly distinguished.
>
> 5\. Support an exact, auditable year-to-base adjustment waterfall.
>
> 6\. Give every plotted value a corresponding tabular value.
>
> 7\. Remain deterministic and fully usable without external network access.
>
> 8\. Use the backend calculation result as authoritative. The browser may reshape and format data, but it shall not independently recalculate economic results.

# 3. Non-goals for the MVP

The following are explicitly outside the MVP:

- linked brushing or synchronized hover highlighting across charts;

- contribution analysis between two arbitrary non-base years;

- live BLS retrieval, snapshot refresh, or data ingestion;

- editing component weights from the result view;

- dual-axis charts;

- smoothing or interpolation of PPI observations;

- silently filling missing observations with zero; and

- a Power BI-equivalent interaction model.

The custom legend is the required component-selection control. Selecting a component by clicking a chart segment is an optional enhancement, not an acceptance requirement.

# 4. Definitions and calculation rules

## 4.1 Symbols

For component i and period t:

- P(i,t) = raw PPI observation.

- B(i) = the component's base-year normalization value.

- N(i,t) = normalized component factor.

- w(i) = fixed allocation weight.

- A(i,t) = weighted component level.

- I(t) = custom composite index factor.

## 4.2 Normalized component factor

> N(i,t) = P(i,t) / B(i)

For the annual base-year value used by this view:

> N(i,base year) = 1.0

If a later implementation displays monthly observations while using a base-year annual average, individual months within the base year need not equal 1.0. The annual average remains the normalization anchor.

## 4.3 Allocation weights

> sum(w(i)) = 1.0

Weights are stored and returned as decimal factors, such as 0.35. They are displayed to users as percentages, such as 35%.

## 4.4 Weighted component level

> A(i,t) = w(i) \* N(i,t)

The stacked area chart plots A(i,t). It does not plot the raw PPI, the unweighted normalized factor, or a contribution-to-change percentage.

## 4.5 Composite index

> I(t) = sum(A(i,t))  
> = sum(w(i) \* N(i,t))

Because all components equal 1.0 at the annual base-year anchor and the weights sum to 1.0:

> I(base year) = 1.0

The black composite line must equal the top of the stacked area at every period within the configured numeric tolerance.

## 4.6 Detail-chart display

The canonical normalized value remains a factor. The detail chart formats that factor as percent of base:

> 1.00 -\> 100%  
> 1.08 -\> 108%  
> 0.94 -\> 94%

No new calculation is implied by this formatting.

## 4.7 Adjustment from a selected year to the base year

Let y be the selected source year and b the base year. Since I(b) = 1.0, the basket-level adjustment factor from year y to the base year is:

> F(y -\> b) = I(b) / I(y)  
> = 1.0 / I(y)

The total adjustment percentage is:

> Adjustment % = F(y -\> b) - 1.0

The exact component contribution to that adjustment factor is:

> D(i,y -\> b) = w(i) \* (1.0 - N(i,y)) / I(y)

The contributions reconcile exactly:

> 1.0 + sum(D(i,y -\> b)) = F(y -\> b)

The waterfall therefore starts at 1.0 (displayed as 100% of the selected-year basket), adds each component's adjustment contribution, and ends at F(y -\> b).

This is intentionally different from a bridge that starts at I(y) and ends at 1.0. The specified waterfall explains the multiplicative adjustment actually applied to a selected-year amount.

If the selected year is later than the base year, some or all contributions may be negative and the ending adjustment factor may be below 1.0. The UI shall use the neutral term **Adjustment to base year** rather than assuming the result is always an escalation.

# 5. Information architecture and layout

## 5.1 Recommended layout

> +------------------------------------------------------------------+  
> \| Index title \| Base year \| Frequency \| Snapshot / methodology \|  
> +------------------------------------------------------------------+  
> \| Allocation ribbon: stacked horizontal bar \|  
> \| Custom clickable legend with PPI names and allocation weights \|  
> +------------------------------------------------------------------+  
> \| Weighted component levels \|  
> \| Stacked area chart + solid black composite line \|  
> +------------------------------------------------------------------+  
> \| Component detail \| Adjustment to base year \| Data \|  
> \| Tabbed or vertically stacked lower section \|  
> +------------------------------------------------------------------+

The allocation display shall be placed above the main chart. This preserves horizontal width for time-series data and avoids competing with the main chart's Y-axis.

## 5.2 Primary app state

The result view requires the following UI state:

> selected_component_id  
> selected_source_year (optional)  
> detail_mode = normalized_percent \| raw  
> active_table_filters

Hover state may be used for ordinary native tooltips, but it shall not drive cross-chart highlighting.

# 6. Functional requirements

## 6.1 Header and calculation identity

> **FR-001** The view shall display the custom index name.
>
> **FR-002** The view shall display the base year and state that the annual base-year factor is 1.0.
>
> **FR-003** The view shall display the observation frequency and normalization method.
>
> **FR-004** The view shall expose the exact specification revision, snapshot identity, and methodology version through visible metadata or an expandable information area.
>
> **FR-005** Warnings that materially affect interpretation shall appear above the charts and in the exported data where applicable.

## 6.2 Allocation ribbon

> **FR-010** The allocation basis shall be shown as one thin horizontal stacked bar.
>
> **FR-011** Each segment width shall equal the component allocation weight.
>
> **FR-012** The segments shall sum to 100% within the configured weight tolerance.
>
> **FR-013** Segment order shall match the component display order used in the legend, stacked area, waterfall, and table.
>
> **FR-014** Each component shall receive one stable display color for the life of the rendered result.
>
> **FR-015** Black shall be reserved for the composite line and waterfall total bars. Component colors shall not use black.
>
> **FR-016** A segment tooltip shall show, at minimum, component name, series ID, allocation percentage, and short description when the chart implementation supports segment tooltips.

## 6.3 Custom legend and component selection

> **FR-020** A custom legend shall appear directly below or beside the allocation ribbon.
>
> **FR-021** Each legend item shall be a focusable, clickable control, not color-only text.
>
> **FR-022** Each legend item shall contain the component color marker, component name, and allocation percentage.
>
> **FR-023** Clicking or keyboard-activating a legend item shall set selected_component_id and update the detail panel without recalculating the composite index.
>
> **FR-024** The selected legend item shall have a non-color visual state, such as an outline, check mark, or selected badge.
>
> **FR-025** The initial selected component shall be the first component in display order unless the app is opened with an explicit component selection.
>
> **FR-026** Clicking a ribbon segment or stacked-area band may also select a component if the installed chart component provides a stable event. This behavior is optional for the MVP.
>
> **FR-027** Hovering one element shall not be required to highlight corresponding elements elsewhere. Linked brushing is out of scope.

## 6.4 Main weighted stacked-area chart

> **FR-030** The main chart shall be a stacked area chart ordered chronologically on the X-axis.
>
> **FR-031** Each area shall plot the weighted component level A(i,t) = w(i) \* N(i,t).
>
> **FR-032** A solid black line shall plot the composite factor I(t).
>
> **FR-033** The black line shall coincide with the top of the stack within numeric tolerance for every period.
>
> **FR-034** The Y-axis shall be labeled or described as a composite factor with base-year annual average equal to 1.0.
>
> **FR-035** The chart shall use straight segments between observations. Smoothing is prohibited.
>
> **FR-036** Missing required observations shall produce a visible error or gap according to the calculation contract. They shall never be replaced by zero or silently interpolated.
>
> **FR-037** The default tooltip for a component area shall include:

- period;

- component name and series ID;

- allocation weight;

- raw PPI value;

- normalized factor and percent-of-base display; and

- weighted component level.

> **FR-038** The composite-line tooltip shall include the period and composite factor. It may also show the factor as percent of base for readability.
>
> **FR-039** The chart legend supplied by the chart library may be hidden if it duplicates the custom legend.

## 6.5 Selected-component detail

> **FR-040** The detail section shall display the selected component name, description, series ID, allocation weight, raw PPI reference basis, and normalization basis.
>
> **FR-041** The detail chart shall plot the selected component without applying its allocation weight.
>
> **FR-042** The default detail mode shall be **Normalized (%)**.
>
> **FR-043** In normalized mode, the Y-axis and tooltips shall display 100 \* N(i,t) percent, so the base-year anchor displays as 100%.
>
> **FR-044** A horizontal reference at 100% shall be shown where supported.
>
> **FR-045** A **Raw PPI** mode shall be available as a toggle or segmented control.
>
> **FR-046** Raw mode shall plot P(i,t) and display the source series' original reference basis. Raw values shall not be compared across components on a shared axis.
>
> **FR-047** The detail chart should use a line with a light area fill. The line is authoritative; the fill is decorative.
>
> **FR-048** The normalized and raw series shall not be displayed simultaneously on dual axes.

## 6.6 Adjustment-to-base waterfall

> **FR-050** The app shall provide an **Adjustment to base year** view.
>
> **FR-051** The user shall select one source year from the set of complete, eligible years in the calculation result.
>
> **FR-052** The waterfall shall use annual values produced by the same methodology used for base-year normalization. If the main series is monthly or quarterly, annual values must be resolved by the backend before the waterfall is returned.
>
> **FR-053** The waterfall start total shall be 1.0, displayed as 100% of the selected-year basket.
>
> **FR-054** Each component step shall equal D(i,y -\> b) and shall be displayed as percentage points of the selected-year basket.
>
> **FR-055** The ending total shall be F(y -\> b) = 1.0 / I(y).
>
> **FR-056** The sum of the displayed component steps shall reconcile to the ending total within numeric tolerance.
>
> **FR-057** Component bars shall use the same colors as the allocation ribbon and main chart. Start and end totals shall be black or a neutral total color.
>
> **FR-058** The default waterfall order shall match the allocation display order. Sorting by absolute impact may be added later.
>
> **FR-059** Positive and negative values shall retain their signs in labels and tooltips.
>
> **FR-060** The waterfall tooltip shall include:

- component name;

- allocation weight;

- selected-year normalized factor;

- index-level difference to the base year;

- adjustment-factor contribution; and

- displayed percentage-point contribution.

> **FR-061** If the selected year equals the base year, the view shall show a zero-adjustment state rather than a visually meaningless waterfall.
>
> **FR-062** If any required selected-year observation is missing, the waterfall shall be unavailable and shall show a structured explanation. No partial waterfall is permitted.

## 6.7 Data table

> **FR-070** The app shall provide a filterable and sortable data table containing one row per component-period observation.
>
> **FR-071** The table shall include at least these columns:

| **Column**         | **Meaning**                                    |
|--------------------|------------------------------------------------|
| period             | Canonical period identifier or label           |
| component_name     | Human-readable component name                  |
| component_id       | Stable application identifier                  |
| series_id          | BLS series identifier                          |
| allocation_weight  | Decimal weight; displayed as percent           |
| raw_ppi_value      | Source observation                             |
| normalized_factor  | Unweighted factor, base-year anchor = 1.0      |
| normalized_percent | Display value, 100 \* normalized_factor        |
| weighted_level     | allocation_weight \* normalized_factor         |
| composite_factor   | Composite factor for the same period           |
| base_year          | Normalization base year                        |
| snapshot_id        | Snapshot identity                              |
| observation_id     | Stable source-observation or ledger identifier |

> **FR-072** Long descriptions and detailed provenance may appear in expandable row content rather than permanent columns.
>
> **FR-073** Default row order shall be period ascending, then component display order (by weight, descending).
>
> **FR-074** Values displayed in the table may be rounded for readability, but the underlying row model shall retain canonical decimal precision.

## 6.8 Table export

> **FR-080** The table shall include an **Export CSV** action.
>
> **FR-081** Export shall include all rows matching the active filters, not merely the current paginated page.
>
> **FR-082** Export row order shall match the table's active deterministic sort order.
>
> **FR-083** The exported CSV shall use UTF-8 encoding. A UTF-8 byte-order mark may be included for spreadsheet compatibility.
>
> **FR-084** Exported numeric fields shall use invariant dot-decimal notation and shall not contain display-only thousands separators.
>
> **FR-085** The export shall include canonical factor columns and may include separate human-readable percent columns. Percent columns shall be numeric, such as 108.25, rather than strings containing %.
>
> **FR-086** The export shall use the authoritative table-row data already returned by the backend or Pydantic adapter. It shall not recalculate values in JavaScript.
>
> **FR-087** The suggested file name is:
>
> custom-index\_\<spec-id\>\_rev-\<revision\>\_base-\<year\>\_\<snapshot-short-id\>.csv
>
> **FR-088** User-entered text fields shall be escaped to prevent spreadsheet formula injection. Values beginning with =, +, -, or @ shall be safely encoded when exported as text.
>
> **FR-089** Export shall work offline and shall not load an external library or service at click time.

# 7. Prefab-oriented implementation notes

The preferred implementation uses native Prefab layout, state, controls, and table elements. Chart requirements should be mapped to the installed Prefab component schemas rather than assumed from examples written for another version.

Recommended mapping:

| **Requirement**    | **Preferred UI element**                                                             |
|--------------------|--------------------------------------------------------------------------------------|
| Header and summary | Cards, headings, badges, text                                                        |
| Allocation ribbon  | Horizontal stacked bar                                                               |
| Clickable legend   | Row or wrapping grid of button-like legend controls                                  |
| Main visualization | Stacked area plus composite line, or a composed/custom chart surface                 |
| Detail chart       | Line chart with optional area fill                                                   |
| Detail-mode toggle | Tabs or segmented control                                                            |
| Waterfall          | Stacked-column emulation with an invisible offset series and custom component series |
| Data view          | Data table                                                                           |
| Export             | Button invoking client-side CSV generation or an app backend export action           |

If the installed Prefab chart components cannot combine a stacked area and line in one native chart, the main visualization may use one self-contained embedded chart surface while the surrounding controls and data table remain native Prefab. Or the area data may be augmented with a “dummy” series for the composite that natively extends the area chart with a black line atop it.

## 7.1 Waterfall chart shaping

The canonical backend response shall return semantic waterfall steps. The Pydantic view-model adapter may transform them into chart-specific rows.

For each component step:

> previous = running factor before the step  
> current = previous + component adjustment contribution  
> offset = min(previous, current)  
> height = abs(component adjustment contribution)

A chart-ready row may contain:

> label  
> step_type = start \| component \| end  
> offset  
> component-specific height field  
> total  
> signed_delta  
> running_factor

The invisible offset series makes each component bar float between the previous and current running factor. Separate component-specific series allow each step to use the component's assigned color. Start and end rows use the total series.

Chart-specific dynamic keys belong only in the presentation adapter. They should not be the authoritative service contract.

# 8. Recommended return-data format

## 8.1 Recommendation

Return one **versioned JSON object in canonical long form**.

Use:

- stable component and period identifiers;

- arrays of typed records rather than dynamic component names as object keys;

- decimal strings for authoritative numeric values;

- explicit metadata and provenance;

- an optional semantic base-year-adjustment object; and

- no chart-library-specific offsets, spacer series, or dynamic wide fields in the core result.

This format is the best fit because it is:

- straightforward to validate with Pydantic;

- stable when components are added, removed, or renamed;

- easy to pivot into the wide rows often expected by chart libraries;

- directly usable for the long-form data table and CSV export;

- friendly to Decimal arithmetic; and

- less likely to turn presentation concerns into a permanent API contract.

The Pydantic adapter should reshape data for Prefab. It should not recompute normalized factors, weighted levels, composite factors, or waterfall contributions.

## 8.2 Authoritative payload structure

> IndexVisualizationData  
> schema_version  
> index_identity  
> normalization  
> components\[\]  
> component_points\[\]  
> composite_points\[\]  
> base_year_adjustment (optional)  
> warnings\[\]

## 8.3 Suggested Pydantic model outline

> from \_\_future\_\_ import annotations  
>   
> from decimal import Decimal  
> from typing import Literal  
>   
> from pydantic import BaseModel, ConfigDict, Field  
>   
>   
> class StrictModel(BaseModel):  
> model_config = ConfigDict(extra="forbid", frozen=True)  
>   
>   
> class IndexIdentity(StrictModel):  
> index_id: str  
> name: str  
> spec_id: str  
> spec_revision: int  
> snapshot_id: str  
> methodology_version: str  
> frequency: Literal\["annual", "quarterly", "monthly"\]  
>   
>   
> class NormalizationBasis(StrictModel):  
> base_year: int  
> base_factor: Decimal = Decimal("1.0")  
> method: Literal\["base_year_annual_average"\]  
>   
>   
> class ComponentDefinition(StrictModel):  
> component_id: str  
> display_order: int = Field(ge=0)  
> name: str  
> description: str  
> series_id: str  
> allocation_weight: Decimal = Field(ge=0, le=1)  
> raw_unit: str \| None = None  
> raw_reference_basis: str \| None = None  
> color_hex: str \| None = None \# Presentation metadata only  
>   
>   
> class ComponentPoint(StrictModel):  
> period: str  
> year: int  
> period_kind: Literal\["annual_average", "quarter", "month"\]  
> component_id: str  
> raw_ppi_value: Decimal  
> normalized_factor: Decimal  
> weighted_level: Decimal  
> observation_id: str  
>   
>   
> class CompositePoint(StrictModel):  
> period: str  
> year: int  
> period_kind: Literal\["annual_average", "quarter", "month"\]  
> composite_factor: Decimal  
>   
>   
> class AdjustmentStep(StrictModel):  
> component_id: str  
> display_order: int  
> selected_year_normalized_factor: Decimal  
> index_level_delta: Decimal  
> adjustment_contribution: Decimal  
> running_adjustment_factor: Decimal  
>   
>   
> class BaseYearAdjustment(StrictModel):  
> source_year: int  
> base_year: int  
> source_composite_factor: Decimal  
> adjustment_factor: Decimal  
> adjustment_percent: Decimal  
> steps: tuple\[AdjustmentStep, ...\]  
>   
>   
> class Finding(StrictModel):  
> code: str  
> severity: Literal\["info", "warning", "error"\]  
> message: str  
>   
>   
> class IndexVisualizationData(StrictModel):  
> schema_version: Literal\["1.0"\]  
> index_identity: IndexIdentity  
> normalization: NormalizationBasis  
> components: tuple\[ComponentDefinition, ...\]  
> component_points: tuple\[ComponentPoint, ...\]  
> composite_points: tuple\[CompositePoint, ...\]  
> base_year_adjustment: BaseYearAdjustment \| None = None  
> warnings: tuple\[Finding, ...\] = ()

The exact model names are not normative. The boundaries are.

## 8.4 Numeric serialization

Authoritative decimal values should be serialized as JSON strings, for example:

> {  
> "allocation_weight": "0.350000",  
> "normalized_factor": "1.082500",  
> "weighted_level": "0.378875",  
> "composite_factor": "1.064210"  
> }

Pydantic should parse these fields into Decimal. The final chart adapter may convert validated display values to JavaScript numbers. That conversion occurs only after the authoritative decimal calculations have been completed and validated.

## 8.5 Example payload

> {  
> "schema_version": "1.0",  
> "index_identity": {  
> "index_id": "courthouse-renovation",  
> "name": "Courthouse Renovation Escalation Index",  
> "spec_id": "courthouse-renovation",  
> "spec_revision": 3,  
> "snapshot_id": "sha256:example",  
> "methodology_version": "composite-index/1.0",  
> "frequency": "annual"  
> },  
> "normalization": {  
> "base_year": 2024,  
> "base_factor": "1.0",  
> "method": "base_year_annual_average"  
> },  
> "components": \[  
> {  
> "component_id": "steel",  
> "display_order": 0,  
> "name": "Steel mill products",  
> "description": "Producer prices for selected steel mill products.",  
> "series_id": "WPU1017",  
> "allocation_weight": "0.400000",  
> "raw_unit": "index",  
> "raw_reference_basis": "BLS published basis",  
> "color_hex": "#4C78A8"  
> },  
> {  
> "component_id": "electrical",  
> "display_order": 1,  
> "name": "Electrical equipment",  
> "description": "Producer prices for selected electrical equipment.",  
> "series_id": "WPU117",  
> "allocation_weight": "0.600000",  
> "raw_unit": "index",  
> "raw_reference_basis": "BLS published basis",  
> "color_hex": "#F58518"  
> }  
> \],  
> "component_points": \[  
> {  
> "period": "2023",  
> "year": 2023,  
> "period_kind": "annual_average",  
> "component_id": "steel",  
> "raw_ppi_value": "271.400",  
> "normalized_factor": "0.940000",  
> "weighted_level": "0.376000",  
> "observation_id": "obs:steel:2023"  
> },  
> {  
> "period": "2023",  
> "year": 2023,  
> "period_kind": "annual_average",  
> "component_id": "electrical",  
> "raw_ppi_value": "198.200",  
> "normalized_factor": "0.970000",  
> "weighted_level": "0.582000",  
> "observation_id": "obs:electrical:2023"  
> }  
> \],  
> "composite_points": \[  
> {  
> "period": "2023",  
> "year": 2023,  
> "period_kind": "annual_average",  
> "composite_factor": "0.958000"  
> }  
> \],  
> "base_year_adjustment": {  
> "source_year": 2023,  
> "base_year": 2024,  
> "source_composite_factor": "0.958000",  
> "adjustment_factor": "1.0438413361",  
> "adjustment_percent": "0.0438413361",  
> "steps": \[  
> {  
> "component_id": "steel",  
> "display_order": 0,  
> "selected_year_normalized_factor": "0.940000",  
> "index_level_delta": "0.024000",  
> "adjustment_contribution": "0.0250521921",  
> "running_adjustment_factor": "1.0250521921"  
> },  
> {  
> "component_id": "electrical",  
> "display_order": 1,  
> "selected_year_normalized_factor": "0.970000",  
> "index_level_delta": "0.018000",  
> "adjustment_contribution": "0.0187891441",  
> "running_adjustment_factor": "1.0438413362"  
> }  
> \]  
> },  
> "warnings": \[\]  
> }

Minor differences in the final decimal place may occur if display examples are rounded. The production validator shall use the configured Decimal precision and tolerance.

## 8.6 Presentation adapter outputs

The Pydantic view-model adapter may derive the following non-authoritative structures:

> allocation_segments\[\]  
> legend_items\[\]  
> area_chart_rows\[\] \# Wide rows, one per period  
> component_detail_rows\[\] \# Selected component only  
> waterfall_chart_rows\[\] \# Offset/height/total chart shape  
> data_table_rows\[\] \# Long-form rows with repeated metadata

Example wide area row:

> {  
> "period": "2023",  
> "steel": 0.376,  
> "electrical": 0.582,  
> "composite": 0.958  
> }

Dynamic component keys are acceptable here because this object exists only at the chart boundary.

# 9. Validation and invariants

The backend or Pydantic model layer shall verify the following before rendering:

> 1\. Component IDs are unique.
>
> 2\. Display order values are unique or deterministically tie-broken.
>
> 3\. Allocation weights sum to 1.0 within the configured tolerance.
>
> 4\. Every component point references a known component.
>
> 5\. There is at most one point per component and canonical period.
>
> 6\. weighted_level = allocation_weight \* normalized_factor within numeric tolerance.
>
> 7\. The sum of weighted levels equals the returned composite factor for each period.
>
> 8\. The annual base-year normalized factor equals 1.0 for every component.
>
> 9\. The annual base-year composite factor equals 1.0.
>
> 10\. All required component-period observations are present before a composite period is rendered.
>
> 11\. The adjustment factor equals 1.0 / source_composite_factor.
>
> 12\. The sum of adjustment contributions equals adjustment_factor - 1.0.
>
> 13\. The final running adjustment factor equals the returned adjustment factor.
>
> 14\. Color assignments are valid CSS colors and are unique where practical.

A failed invariant is an application error, not a warning to be hidden beneath a cheerful chart.

# 10. Accessibility requirements

> **AR-001** Color shall not be the only means of identifying a component. Every component has a text label and stable ID.
>
> **AR-002** Legend items shall be keyboard focusable and activatable.
>
> **AR-003** The selected state shall be communicated through text or control state in addition to color.
>
> **AR-004** Hover tooltips shall have an equivalent keyboard-focus behavior where the component library permits it.
>
> **AR-005** The selected component's name and description shall appear as persistent text in the detail panel. This text is the accessible equivalent of the requested hover description.
>
> **AR-006** Charts shall have concise accessible summaries. The data table shall provide the complete numeric alternative.
>
> **AR-007** The detail-mode control shall expose its current state to assistive technology.
>
> **AR-008** The export action shall have a clear accessible name and shall report success or failure.

# 11. Offline and deterministic behavior

> **NFR-001** All UI assets, chart code, fonts, and export logic shall be bundled locally. No CDN dependency is permitted.
>
> **NFR-002** The result view shall not initiate BLS traffic or any other external HTTP request.
>
> **NFR-003** Identical calculation input, snapshot identity, and methodology version shall produce identical canonical payloads, excluding explicitly non-deterministic operational metadata.
>
> **NFR-004** Browser-side code may format values and reshape validated records. It shall not perform authoritative normalization, weighting, composite calculation, or waterfall calculation.
>
> **NFR-005** The app shall use Decimal arithmetic before presentation conversion.
>
> **NFR-006** Chart and table ordering shall be deterministic.

# 12. Error and empty states

The UI shall provide specific states for:

- no calculation result;

- invalid or incomplete weight total;

- missing base-year observations;

- missing period observations;

- unknown selected component;

- unavailable source year for the waterfall;

- failed calculation invariant;

- no table rows after filtering; and

- export failure.

Errors shall name the affected component, period, and invariant where available. Missing data shall never be shown as zero.

# 13. Acceptance criteria

The feature is accepted when all of the following are true:

> 1\. The allocation ribbon widths reconcile to 100%.
>
> 2\. Component names, order, and colors are consistent across the ribbon, custom legend, main chart, detail view, waterfall, and table.
>
> 3\. Selecting a legend item updates the detail panel and chart without a server-side recalculation of the composite.
>
> 4\. The main stacked areas plot weighted component levels.
>
> 5\. The black line matches the top of the stack for every rendered period.
>
> 6\. The annual base-year composite is 1.0.
>
> 7\. The detail chart defaults to normalized-percent display and shows the base-year anchor as 100%.
>
> 8\. Raw mode shows the original PPI values and reference basis.
>
> 9\. Selecting an eligible source year produces a waterfall that starts at 100%, reconciles through component contributions, and ends at the exact adjustment factor.
>
> 10\. The waterfall handles negative contributions and post-base years correctly.
>
> 11\. The table contains one row per component-period and values reconcile to the charts.
>
> 12\. CSV export includes all filtered rows, uses canonical numeric values, works offline, and is not limited to the visible page.
>
> 13\. Keyboard users can select components, change detail mode, choose a source year, and export data.
>
> 14\. Blocking network access does not impair the result view.
>
> 15\. Invalid or missing source data produces an explicit error rather than a plausible-looking chart.

# 14. Future enhancements

Potential later additions include:

- optional chart-segment selection;

- linked brushing and synchronized hover state;

- sorting waterfall steps by absolute impact;

- contribution analysis between arbitrary periods;

- downloadable full audit package containing JSON, CSV, and provenance files;

- image export of the current chart view;

- user-selectable component visibility; and

- saved presentation preferences.

These enhancements shall not alter the canonical calculation contract defined here.
