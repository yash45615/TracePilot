import { useCallback, useEffect, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000/api/v1";

type Release = {
  id: number;
  version: string;
  name: string;
  description?: string | null;
  created_at?: string | null;
};

type Investigation = {
  id: number;
  title: string;
  question: string;
  status: string;
  created_at?: string | null;
};

type Metrics = {
  release_id: number;
  release_version: string;
  total_events: number;
  unique_users: number;
  conversion_rate: number;
  error_rate: number;
  average_duration_ms: number;
};

type RegressionAssessment = {
  status: string;
  reason?: string | null;
  baseline_error_rate?: number | null;
  candidate_error_rate?: number | null;
  change_percentage_points?: number | null;
  p_value?: number | null;
  alpha?: number | null;
  minimum_increase_percentage_points?: number | null;
  baseline_ci_95?: number[] | null;
  candidate_ci_95?: number[] | null;
};

type Comparison = {
  baseline: Metrics;
  candidate: Metrics;
  conversion_change_percentage_points: number;
  error_rate_change_percentage_points: number;
  average_duration_change_ms: number;
  interpretation?: string[];
  regression_assessment?: RegressionAssessment | null;
};

type EvidenceReference = {
  evidence_id: number;
  title?: string | null;
  evidence_type?: string | null;
  source?: string | null;
};

type InvestigationFinding = {
  investigation_id: number;
  investigation_title?: string | null;
  investigation_status?: string | null;
  question?: string | null;
  conclusion?: string | null;
  evidence_quality?: string | null;
  explanation?: string | null;
  evidence_count?: number;
  valid_assessment_count?: number;
  evidence_references?: EvidenceReference[];
  limitations?: string[];
};

type EvidenceRecord = {
  id: number;
  investigation_id?: number | null;
  evidence_type: string;
  title: string;
  description?: string | null;
  source?: string | null;
  data?: Record<string, unknown>;
  created_at?: string | null;
};

type InvestigationSummary = {
  investigation_id?: number;
  title?: string;
  evidence_count?: number;
  evidence?: EvidenceRecord[];
  caveats?: string[];
  [key: string]: unknown;
};

type ApiList<T> = {
  value?: T[];
  Count?: number;
  count?: number;
};

type StatCardProps = {
  label: string;
  value: string | number;
  description: string;
};

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);

  if (!response.ok) {
    let message = `Request failed (${response.status})`;

    try {
      const body = (await response.json()) as {
        detail?: string | { msg?: string }[];
      };

      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((item) => item.msg ?? "Validation error").join(", ");
      }
    } catch {
      // Keep the HTTP status message if the response has no JSON body.
    }

    throw new Error(message);
  }

  return (await response.json()) as T;
}

function unwrapList<T>(response: T[] | ApiList<T>): T[] {
  if (Array.isArray(response)) {
    return response;
  }

  return response.value ?? [];
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }

  return value.toLocaleString("en-IN", {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  });
}

function formatDate(value?: string | null): string {
  if (!value) {
    return "Date unavailable";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase().replaceAll(" ", "_");

  return (
    <span className={`status-pill status-${normalized}`}>
      {formatLabel(status)}
    </span>
  );
}

function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="panel-heading">
      <span className="section-eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      {description && <p>{description}</p>}
    </div>
  );
}

function StatCard({ label, value, description }: StatCardProps) {
  return (
    <article className="stat-card">
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      <span className="stat-description">{description}</span>
    </article>
  );
}

function MetricTile({
  label,
  value,
  change,
  suffix = "",
}: {
  label: string;
  value: number;
  change?: number;
  suffix?: string;
}) {
  const hasChange = change !== undefined && Number.isFinite(change);

  return (
    <article className="metric-tile">
      <span>{label}</span>
      <strong>
        {formatNumber(value)}
        {suffix}
      </strong>
      {hasChange && (
        <small className={change > 0 ? "metric-negative" : change < 0 ? "metric-positive" : ""}>
          {change > 0 ? "+" : ""}
          {formatNumber(change)}
          {suffix} change
        </small>
      )}
    </article>
  );
}

export default function App() {
  const [releases, setReleases] = useState<Release[]>([]);
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [comparison, setComparison] = useState<Comparison | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dashboardError, setDashboardError] = useState("");

  const [selectedInvestigationId, setSelectedInvestigationId] =
    useState<number | null>(null);
  const [investigationSummary, setInvestigationSummary] =
    useState<InvestigationSummary | null>(null);
  const [investigationFindings, setInvestigationFindings] =
    useState<InvestigationFinding | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  const loadDashboard = useCallback(async () => {
    setRefreshing(true);
    setDashboardError("");

    try {
      const [releaseResponse, investigationResponse] = await Promise.all([
        fetchJson<Release[] | ApiList<Release>>("/releases"),
        fetchJson<Investigation[] | ApiList<Investigation>>("/investigations"),
      ]);

      const releaseItems = unwrapList(releaseResponse);
      const investigationItems = unwrapList(investigationResponse);

      setReleases(releaseItems);
      setInvestigations(investigationItems);

      if (releaseItems.length >= 2) {
        const ordered = [...releaseItems].sort((a, b) => a.id - b.id);
        const baseline = ordered[0];
        const candidate = ordered[ordered.length - 1];

        try {
          const comparisonResult = await fetchJson<Comparison>(
            `/metrics/compare?baseline_id=${baseline.id}&candidate_id=${candidate.id}`,
          );

          setComparison(comparisonResult);
        } catch (error) {
          setComparison(null);
          setDashboardError(
            `Release data loaded, but comparison failed: ${getErrorMessage(error)}`,
          );
        }
      } else {
        setComparison(null);
      }
    } catch (error) {
      setDashboardError(getErrorMessage(error));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (selectedInvestigationId === null) {
      setInvestigationSummary(null);
      setInvestigationFindings(null);
      setDetailError("");
      return;
    }

    let cancelled = false;

    async function loadInvestigationDetails() {
      setDetailLoading(true);
      setDetailError("");
      setInvestigationSummary(null);
      setInvestigationFindings(null);

      const id = selectedInvestigationId;

      const [summaryResult, findingsResult] = await Promise.allSettled([
        fetchJson<InvestigationSummary>(
          `/investigations/${id}/summary`,
        ),
        fetchJson<InvestigationFinding>(
          `/investigations/${id}/findings`,
        ),
      ]);

      if (cancelled) {
        return;
      }

      const errors: string[] = [];

      if (summaryResult.status === "fulfilled") {
        setInvestigationSummary(summaryResult.value);
      } else {
        errors.push(`Summary: ${getErrorMessage(summaryResult.reason)}`);
      }

      if (findingsResult.status === "fulfilled") {
        setInvestigationFindings(findingsResult.value);
      } else {
        errors.push(`Findings: ${getErrorMessage(findingsResult.reason)}`);
      }

      setDetailError(errors.join(" | "));
      setDetailLoading(false);
    }

    void loadInvestigationDetails();

    return () => {
      cancelled = true;
    };
  }, [selectedInvestigationId]);

  const regression = comparison?.regression_assessment;
  const totalEvents =
    comparison === null
      ? 0
      : comparison.baseline.total_events + comparison.candidate.total_events;


  const selectedInvestigation = investigations.find(
    (investigation) => investigation.id === selectedInvestigationId,
  );

  const summaryEvidence = investigationSummary?.evidence;

  const evidenceReferences =
    investigationFindings?.evidence_references ??
    summaryEvidence?.map((evidence) => ({
      evidence_id: evidence.id,
      title: evidence.title,
      evidence_type: evidence.evidence_type,
      source: evidence.source,
    })) ??
    [];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">T</div>
          <div>
            <strong>TracePilot</strong>
            <small>Release intelligence</small>
          </div>
        </div>

        <div className="sidebar-section">
          <span className="sidebar-label">WORKSPACE</span>
          <nav className="navigation" aria-label="Main navigation">
            <a className="nav-item active" href="#overview">
              <span>▦</span>
              Overview
            </a>
            <a className="nav-item" href="#releases">
              <span>⇄</span>
              Releases
            </a>
            <a className="nav-item" href="#investigations">
              <span>⌕</span>
              Investigations
            </a>
          </nav>
        </div>

        <div className="sidebar-bottom">
          <div className="sidebar-status">
            <span className="connection-dot" />
            <div>
              <strong>Local environment</strong>
              <small>API connection status</small>
            </div>
          </div>
          <small className="sidebar-footnote">TracePilot · Developer preview</small>
        </div>
      </aside>

      <main className="main-area">
        <div className="page-content">
          <header className="topbar">
            <div>
              <div className="breadcrumb">Workspace / Overview</div>
              <h1>Release overview</h1>
              <p className="page-subtitle">
                Understand release health, spot regressions, and investigate
                changes with linked evidence.
              </p>
            </div>

            <button
              className="button button-secondary refresh-button"
              type="button"
              onClick={() => void loadDashboard()}
              disabled={refreshing}
            >
              <span aria-hidden="true">↻</span>
              {refreshing ? "Refreshing…" : "Refresh data"}
            </button>
          </header>

          {dashboardError && (
            <div className="alert alert-error" role="alert">
              <strong>Dashboard notice</strong>
              <p>{dashboardError}</p>
            </div>
          )}

          {loading ? (
            <section className="panel loading-panel">
              <div className="loading-indicator" />
              <p>Loading release data from the TracePilot API…</p>
            </section>
          ) : (
            <>
              <section className="stats-grid" id="overview">
                <StatCard
                  label="Tracked releases"
                  value={releases.length}
                  description="Releases returned by the API"
                />
                <StatCard
                  label="Investigations"
                  value={investigations.length}
                  description="Recorded investigation cases"
                />
                <StatCard
                  label="Events compared"
                  value={totalEvents}
                  description="Events across the two compared releases"
                />
                <StatCard
                  label="Regression assessment"
                  value={
                    regression
                      ? formatLabel(regression.status)
                      : "Unavailable"
                  }
                  description={
                    regression?.reason ??
                    "A release comparison is needed to assess regression risk"
                  }
                />
              </section>

              <div className="content-grid">
                <section className="panel release-panel" id="releases">
                  <SectionHeader
                    eyebrow="RELEASE MONITORING"
                    title="Tracked releases"
                    description="Release versions currently available in your API."
                  />

                  {releases.length > 0 ? (
                    <div className="release-list">
                      {releases.map((release) => (
                        <article className="release-row" key={release.id}>
                          <div className="release-icon" aria-hidden="true">
                            ↗
                          </div>
                          <div className="release-details">
                            <strong>{release.name || `Release ${release.version}`}</strong>
                            <span>Version {release.version}</span>
                            {release.description && <small>{release.description}</small>}
                            {release.created_at && (
                              <small>Created {formatDate(release.created_at)}</small>
                            )}
                          </div>
                          <span className="release-tag">#{release.id}</span>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-state">
                      No releases were returned. Add releases through the API to
                      begin comparing versions.
                    </p>
                  )}
                </section>

                <section className="panel investigations-panel" id="investigations">
                  <SectionHeader
                    eyebrow="INVESTIGATION WORKSPACE"
                    title="Recent investigations"
                    description="Open a case to inspect its assessment and linked evidence."
                  />

                  {investigations.length > 0 ? (
                    <div className="investigation-list">
                      {investigations.map((investigation) => (
                        <article
                          className="investigation-row"
                          key={investigation.id}
                        >
                          <div className="investigation-icon" aria-hidden="true">
                            ◎
                          </div>
                          <div className="investigation-details">
                            <strong>{investigation.title}</strong>
                            <span>{investigation.question}</span>
                            <small>
                              Investigation #{investigation.id}
                              {investigation.created_at
                                ? ` · ${formatDate(investigation.created_at)}`
                                : ""}
                            </small>
                            <button
                              className="text-button investigation-view-button"
                              type="button"
                              onClick={() =>
                                setSelectedInvestigationId(investigation.id)
                              }
                            >
                              View investigation details →
                            </button>
                          </div>
                          <StatusPill status={investigation.status} />
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-state">
                      No investigations yet. Create one using the backend API.
                    </p>
                  )}
                </section>

                <section className="panel comparison-panel">
                  <SectionHeader
                    eyebrow="RELEASE ANALYSIS"
                    title="Release comparison"
                    description="Compare baseline and candidate metrics to identify potential regressions."
                  />

                  {comparison ? (
                    <>
                      <div className="comparison-labels">
                        <div className="comparison-release">
                          <span>BASELINE</span>
                          <strong>{comparison.baseline.release_version}</strong>
                          <small>
                            {comparison.baseline.total_events} events
                          </small>
                        </div>

                        <div className="comparison-arrow" aria-hidden="true">
                          →
                        </div>

                        <div className="comparison-release candidate-release">
                          <span>CANDIDATE</span>
                          <strong>{comparison.candidate.release_version}</strong>
                          <small>
                            {comparison.candidate.total_events} events
                          </small>
                        </div>
                      </div>

                      <div className="metric-grid">
                        <MetricTile
                          label="Error rate"
                          value={comparison.candidate.error_rate}
                          suffix="%"
                          change={comparison.error_rate_change_percentage_points}
                        />
                        <MetricTile
                          label="Conversion rate"
                          value={comparison.candidate.conversion_rate}
                          suffix="%"
                          change={comparison.conversion_change_percentage_points}
                        />
                        <MetricTile
                          label="Average duration"
                          value={comparison.candidate.average_duration_ms}
                          suffix=" ms"
                          change={comparison.average_duration_change_ms}
                        />
                        <MetricTile
                          label="Unique users"
                          value={comparison.candidate.unique_users}
                        />
                      </div>

                      {comparison.interpretation &&
                        comparison.interpretation.length > 0 && (
                          <div className="interpretation-block">
                            <h3>Metric interpretation</h3>
                            <ul>
                              {comparison.interpretation.map((item, index) => (
                                <li key={`${index}-${item}`}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                      <div className="assessment-block">
                        <div className="assessment-heading">
                          <div>
                            <span className="section-eyebrow">
                              STATISTICAL CHECK
                            </span>
                            <h3>Regression assessment</h3>
                          </div>
                          <StatusPill
                            status={regression?.status ?? "unavailable"}
                          />
                        </div>

                        <p className="assessment-reason">
                          {regression?.reason ??
                            "The API did not return a regression assessment."}
                        </p>

                        {regression && (
                          <div className="assessment-details">
                            <div>
                              <span>Baseline error rate</span>
                              <strong>
                                {formatNumber(regression.baseline_error_rate)}%
                              </strong>
                            </div>
                            <div>
                              <span>Candidate error rate</span>
                              <strong>
                                {formatNumber(regression.candidate_error_rate)}%
                              </strong>
                            </div>
                            <div>
                              <span>Change</span>
                              <strong>
                                {regression.change_percentage_points !== null &&
                                regression.change_percentage_points !== undefined &&
                                regression.change_percentage_points > 0
                                  ? "+"
                                  : ""}
                                {formatNumber(
                                  regression.change_percentage_points,
                                )}{" "}
                                pp
                              </strong>
                            </div>
                            <div>
                              <span>p-value</span>
                              <strong>{formatNumber(regression.p_value, 6)}</strong>
                            </div>
                          </div>
                        )}

                        <p className="assessment-disclaimer">
                          A statistical regression signal does not establish
                          the cause of a problem. Verify the result against
                          application logs, traces, deployments, and other
                          relevant evidence.
                        </p>
                      </div>
                    </>
                  ) : (
                    <p className="empty-state">
                      Comparison data is unavailable. Make sure at least two
                      releases exist and the metrics comparison endpoint is
                      working.
                    </p>
                  )}
                </section>

                {selectedInvestigationId !== null && (
                  <section className="panel investigation-detail-panel">
                    <div className="detail-header">
                      <SectionHeader
                        eyebrow={`INVESTIGATION #${selectedInvestigationId}`}
                        title={
                          investigationFindings?.investigation_title ??
                          selectedInvestigation?.title ??
                          "Investigation details"
                        }
                        description={
                          investigationFindings?.question ??
                          selectedInvestigation?.question ??
                          "Review the stored evidence and current assessment."
                        }
                      />

                      <button
                        className="button button-secondary"
                        type="button"
                        onClick={() => setSelectedInvestigationId(null)}
                      >
                        Close
                      </button>
                    </div>

                    {detailLoading && (
                      <p className="empty-state">
                        Loading investigation details…
                      </p>
                    )}

                    {detailError && (
                      <div className="alert alert-error" role="alert">
                        <strong>Some details could not be loaded.</strong>
                        <p>{detailError}</p>
                      </div>
                    )}

                    {!detailLoading && investigationFindings && (
                      <>
                        <div className="detail-status-row">
                          <div>
                            <span className="detail-label">
                              Investigation status
                            </span>
                            <StatusPill
                              status={
                                investigationFindings.investigation_status ??
                                selectedInvestigation?.status ??
                                "unknown"
                              }
                            />
                          </div>
                          <div>
                            <span className="detail-label">Conclusion</span>
                            <StatusPill
                              status={
                                investigationFindings.conclusion ?? "unknown"
                              }
                            />
                          </div>
                          <div>
                            <span className="detail-label">Evidence quality</span>
                            <StatusPill
                              status={
                                investigationFindings.evidence_quality ??
                                "unknown"
                              }
                            />
                          </div>
                        </div>

                        <div className="detail-stats">
                          <StatCard
                            label="Linked evidence"
                            value={investigationFindings.evidence_count ?? evidenceReferences.length}
                            description="Evidence records associated with this investigation"
                          />
                          <StatCard
                            label="Valid assessments"
                            value={investigationFindings.valid_assessment_count ?? 0}
                            description="Assessments accepted by the findings engine"
                          />
                        </div>

                        <div className="detail-section">
                          <h3>Current assessment</h3>
                          <p>
                            {investigationFindings.explanation ??
                              "No explanation was returned by the findings endpoint."}
                          </p>
                        </div>

                        <div className="detail-section">
                          <h3>Evidence references</h3>

                          {evidenceReferences.length > 0 ? (
                            <div className="evidence-list">
                              {evidenceReferences.map((evidence) => (
                                <article
                                  className="evidence-card"
                                  key={evidence.evidence_id}
                                >
                                  <div className="evidence-card-heading">
                                    <strong>
                                      {evidence.title ??
                                        `Evidence #${evidence.evidence_id}`}
                                    </strong>
                                    <span className="evidence-id">
                                      #{evidence.evidence_id}
                                    </span>
                                  </div>
                                  <p>
                                    Type:{" "}
                                    {formatLabel(evidence.evidence_type ?? "unknown")}
                                  </p>
                                  {evidence.source && (
                                    <p className="evidence-source">
                                      Source: {evidence.source}
                                    </p>
                                  )}
                                </article>
                              ))}
                            </div>
                          ) : (
                            <p className="empty-state">
                              No evidence references are linked to this
                              investigation.
                            </p>
                          )}
                        </div>

                        <div className="detail-section">
                          <h3>Limitations</h3>
                          {investigationFindings.limitations?.length ? (
                            <ul className="limitations-list">
                              {investigationFindings.limitations.map(
                                (limitation, index) => (
                                  <li key={`${index}-${limitation}`}>
                                    {limitation}
                                  </li>
                                ),
                              )}
                            </ul>
                          ) : (
                            <p>
                              No limitations were returned by the findings
                              endpoint.
                            </p>
                          )}
                        </div>
                      </>
                    )}

                    {!detailLoading &&
                      !investigationFindings &&
                      !detailError && (
                        <p className="empty-state">
                          No findings are available for this investigation.
                        </p>
                      )}
                  </section>
                )}
              </div>
            </>
          )}

          <footer className="page-footer">
            <span>TracePilot · Release intelligence workspace</span>
            <span>
              API: <code>127.0.0.1:8000</code>
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}