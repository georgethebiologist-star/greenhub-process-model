import React from 'react';
import feedCompositionProfile from '../../../Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json';

type AnalyticalMeasurement = {
  id: string;
  label: string;
  value: number | null;
  unit: string;
  basis: string;
  status: 'measured' | 'not_reported';
  data_class: 'A' | null;
};

type AnalyticalEstimate = {
  id: string;
  label: string;
  value: number;
  unit: string;
  basis: string;
  status: 'derived_estimate';
  data_class: 'C';
  calculation: {
    equation: string;
    input_measurement_id: string;
    nitrogen_to_protein_factor: number;
    method_source_id: string;
    method_source_doi: string;
    method_source_location: string;
  };
  limitation: string;
};

type AnalyticalReference = {
  sample_name: string;
  sample_date: string;
  data_class: 'A';
  source: { source_sheet: string; source_row: number; source_id: string };
  measurements: AnalyticalMeasurement[];
  derived_estimates?: AnalyticalEstimate[];
  limitation: string;
};

const reference = (feedCompositionProfile as unknown as { analytical_reference: AnalyticalReference }).analytical_reference;

function displayValue(value: number | null) {
  return value === null
    ? 'Not reported'
    : new Intl.NumberFormat('en-GB', { maximumFractionDigits: 1 }).format(value);
}

export default function FeedAnalyticalReference() {
  const dryMatter = reference.measurements.find((item) => item.id === 'dry_matter_percent')?.value;
  const estimates = reference.derived_estimates ?? [];
  return <details className="feed-analytical-reference">
    <summary>
      <span><strong>Lab reference</strong><small>{reference.sample_name} · {reference.sample_date}</small></span>
      <span className="feed-lab-class" title="Measured project laboratory data">A</span>
    </summary>
    <div className="feed-analytical-content">
      <div className="feed-analytical-grid">
        {reference.measurements.map((measurement) => <div className="feed-analytical-cell" key={measurement.id}>
          <span>{measurement.label}</span>
          <strong>{displayValue(measurement.value)}</strong>
          <small>{measurement.unit}{measurement.data_class === 'A' ? ' · A' : ''}</small>
        </div>)}
        {estimates.map((estimate) => <div className="feed-analytical-cell" key={estimate.id} title={`${estimate.basis} ${estimate.limitation}`}>
          <span>{estimate.label}</span>
          <strong>{displayValue(estimate.value)}</strong>
          <small>{estimate.unit} · C derived estimate</small>
          <small>{estimate.calculation.method_source_id} · DOI {estimate.calculation.method_source_doi}</small>
        </div>)}
      </div>
      <p className="feed-analytical-note">
        {dryMatter}% dry matter is the moisture basis used by the default profile. The other totals are reference measurements, not species-level process inputs. {reference.limitation}
      </p>
      <small className="feed-analytical-source">{reference.source.source_id} · {reference.source.source_sheet}, source row {reference.source.source_row}</small>
    </div>
  </details>;
}
