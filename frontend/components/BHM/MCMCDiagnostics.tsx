"use client";

import { useState, useEffect } from "react";
import { Spinner, Alert, Row, Col, Nav, Tab } from "react-bootstrap";
import { api } from "@/lib/api";
import { API_BASE_URL } from "@/lib/constants";

interface MCMCIterationInfo {
    price?: {
        iterations: {
            total_iterations: number;
            burn_in_iterations: number;
            convergence_iterations: number;
            chains: number;
            draws_per_chain: number;
            warmup_per_chain: number;
            burn_in_percentage: number;
            convergence_percentage: number;
        };
        diagnostics: {
            n_parameters: number;
            max_rhat: number;
            all_converged: boolean;
            n_divergences: number;
            divergence_rate: number;
        };
    };
    timeliness?: {
        iterations: {
            total_iterations: number;
            burn_in_iterations: number;
            convergence_iterations: number;
            chains: number;
            draws_per_chain: number;
            warmup_per_chain: number;
        };
        diagnostics: {
            n_parameters: number;
            max_rhat: number;
            all_converged: boolean;
            n_divergences: number;
            divergence_rate: number;
        };
    };
}

interface MCMCDiagnosticsProps {
    sessionId: string;
}

export default function MCMCDiagnostics({ sessionId }: MCMCDiagnosticsProps) {
    const [iterationInfo, setIterationInfo] =
        useState<MCMCIterationInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState("price");
    const [plotErrors, setPlotErrors] = useState<Record<string, boolean>>({});
    const [plotLoading, setPlotLoading] = useState<Record<string, boolean>>({});
    const [plotTimestamp] = useState(() => Date.now());

    useEffect(() => {
        const fetchIterations = async () => {
            try {
                console.log(
                    `[MCMCDiagnostics] Fetching for session: ${sessionId}`,
                );
                const response = await api.get(
                    `/bhm/mcmc-iterations?session_id=${sessionId}`,
                );
                console.log("[MCMCDiagnostics] Response:", response.data);
                setIterationInfo(response.data);
                setError("");
            } catch (err: any) {
                console.error("[MCMCDiagnostics] Error:", err);
                const errorMessage =
                    err?.response?.data?.detail ||
                    err?.message ||
                    "Failed to load MCMC diagnostics";
                setError(errorMessage);
            } finally {
                setLoading(false);
            }
        };

        if (sessionId) {
            fetchIterations();
        }
    }, [sessionId]);

    if (loading) {
        return (
            <Spinner
                animation="border"
                variant="info"
                className="mx-auto d-block my-5"
            />
        );
    }

    if (error) {
        return <Alert variant="danger">{error}</Alert>;
    }

    if (!iterationInfo) {
        return null;
    }

    const getPlotKey = (metric: string, plot: string) => `${metric}_${plot}`;

    const handlePlotLoad = (key: string) => {
        setPlotLoading((prev) => ({ ...prev, [key]: false }));
        setPlotErrors((prev) => ({ ...prev, [key]: false }));
    };

    const handlePlotError = (key: string) => {
        setPlotLoading((prev) => ({ ...prev, [key]: false }));
        setPlotErrors((prev) => ({ ...prev, [key]: true }));
    };

    const PlotImage = ({
        metricType,
        plotType,
        title,
        description,
    }: {
        metricType: string;
        plotType: string;
        title: string;
        description: string;
    }) => {
        const key = getPlotKey(metricType, plotType);
        const hasError = plotErrors[key];
        const isLoading = plotLoading[key] !== false;

        return (
            <Col lg={12}>
                <div className="card p-3">
                    <h6 className="text-info mb-3">{title}</h6>
                    {isLoading && !hasError && (
                        <div className="text-center py-4">
                            <Spinner
                                animation="border"
                                variant="info"
                                size="sm"
                            />
                            <span className="ms-2 text-muted">
                                Loading plot...
                            </span>
                        </div>
                    )}
                    {hasError && (
                        <Alert variant="warning" className="small mb-0">
                            Failed to load {plotType} plot. The MCMC model may
                            still be processing. Try refreshing the page.
                        </Alert>
                    )}
                    <img
                        src={`${API_BASE_URL}/bhm/mcmc-plots/${metricType}/${plotType}?session_id=${sessionId}&t=${plotTimestamp}`}
                        alt={`${metricType} ${plotType}`}
                        onLoad={() => handlePlotLoad(key)}
                        onError={() => handlePlotError(key)}
                        style={{
                            width: "100%",
                            maxHeight: "600px",
                            objectFit: "contain",
                            display: hasError ? "none" : "block",
                        }}
                    />
                    <small className="text-muted d-block mt-2">
                        {description}
                    </small>
                </div>
            </Col>
        );
    };

    const renderPlots = (metricType: "price" | "timeliness") => (
        <div className="mt-4">
            <Row className="g-4">
                <PlotImage
                    metricType={metricType}
                    plotType="traces"
                    title="📊 Trace Plots (Burn-in Phase)"
                    description="Shows all MCMC chains with burn-in period highlighted in red. Chains should stabilize quickly after burn-in."
                />
                <PlotImage
                    metricType={metricType}
                    plotType="iterations_summary"
                    title="📈 Iteration Summary"
                    description="Shows iteration breakdown, convergence diagnostics (Rhat), and MCMC configuration."
                />
                <PlotImage
                    metricType={metricType}
                    plotType="burnin_analysis"
                    title="🔥 Burn-in Analysis"
                    description="Detailed view of burn-in stabilization. Left shows full trace, right shows zoomed burn-in region."
                />
            </Row>
        </div>
    );

    const renderMetricsTable = (metricType: "price" | "timeliness") => {
        const data = iterationInfo[metricType];
        if (!data) return null;

        return (
            <div className="mt-4">
                <Row className="g-3">
                    <Col lg={6}>
                        <div className="card p-3">
                            <h6 className="text-info mb-3">
                                📊 Iteration Counts
                            </h6>
                            <table className="table table-sm table-borderless">
                                <tbody>
                                    <tr>
                                        <td className="fw-bold">
                                            Total Iterations:
                                        </td>
                                        <td>
                                            {data.iterations.total_iterations.toLocaleString()}{" "}
                                            <small className="text-muted">
                                                (warmup + draws)
                                            </small>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="fw-bold">
                                            Burn-in Iterations:
                                        </td>
                                        <td>
                                            {data.iterations.burn_in_iterations.toLocaleString()}{" "}
                                            (
                                            {data.iterations.burn_in_percentage.toFixed(
                                                1,
                                            )}
                                            %){" "}
                                            <small className="text-muted">
                                                (discarded)
                                            </small>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="fw-bold">
                                            Posterior Samples:
                                        </td>
                                        <td>
                                            {data.iterations.convergence_iterations.toLocaleString()}{" "}
                                            (
                                            {data.iterations.convergence_percentage.toFixed(
                                                1,
                                            )}
                                            %){" "}
                                            <small className="text-muted">
                                                (used for inference)
                                            </small>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="fw-bold">Chains:</td>
                                        <td>{data.iterations.chains}</td>
                                    </tr>
                                    <tr>
                                        <td className="fw-bold">
                                            Warmup per Chain:
                                        </td>
                                        <td>
                                            {data.iterations.warmup_per_chain.toLocaleString()}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="fw-bold">
                                            Draws per Chain:
                                        </td>
                                        <td>
                                            {data.iterations.draws_per_chain.toLocaleString()}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </Col>

                    <Col lg={6}>
                        <div className="card p-3">
                            <h6 className="text-info mb-3">
                                ✅ Convergence Diagnostics
                            </h6>
                            <table className="table table-sm table-borderless">
                                <tbody>
                                    <tr>
                                        <td className="fw-bold">Parameters:</td>
                                        <td>{data.diagnostics.n_parameters}</td>
                                    </tr>
                                    <tr>
                                        <td className="fw-bold">
                                            Max R̂ (Rhat):
                                        </td>
                                        <td>
                                            <span
                                                className={
                                                    data.diagnostics.max_rhat <
                                                    1.01
                                                        ? "text-success"
                                                        : "text-danger"
                                                }
                                            >
                                                {data.diagnostics.max_rhat.toFixed(
                                                    4,
                                                )}
                                            </span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="fw-bold">Status:</td>
                                        <td>
                                            {data.diagnostics.all_converged ? (
                                                <span className="badge bg-success">
                                                    ✓ CONVERGED
                                                </span>
                                            ) : (
                                                <span className="badge bg-warning">
                                                    ⚠ NOT CONVERGED
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="fw-bold">
                                            Divergences:
                                        </td>
                                        <td>
                                            {data.diagnostics.n_divergences}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="fw-bold">
                                            Divergence Rate:
                                        </td>
                                        <td>
                                            {(
                                                data.diagnostics
                                                    .divergence_rate * 100
                                            ).toFixed(3)}
                                            %
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </Col>
                </Row>
            </div>
        );
    };

    return (
        <div className="card p-4 mt-4">
            <h5 className="text-info mb-4">
                ⚙️ MCMC Diagnostics & Burn-in Analysis
            </h5>

            <Tab.Container
                activeKey={activeTab}
                onSelect={(k) => setActiveTab(k || "price")}
            >
                <Nav variant="tabs" className="mb-4">
                    <Nav.Item>
                        <Nav.Link eventKey="price">💰 Price Model</Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                        <Nav.Link eventKey="timeliness">
                            ⏱️ Timeliness Model
                        </Nav.Link>
                    </Nav.Item>
                </Nav>

                <Tab.Content>
                    <Tab.Pane eventKey="price">
                        {renderMetricsTable("price")}
                        {renderPlots("price")}
                    </Tab.Pane>

                    <Tab.Pane eventKey="timeliness">
                        {renderMetricsTable("timeliness")}
                        {renderPlots("timeliness")}
                    </Tab.Pane>
                </Tab.Content>
            </Tab.Container>

            <Alert variant="info" className="mt-4 small">
                <strong>📚 What these mean:</strong>
                <ul className="mb-0 mt-2">
                    <li>
                        <strong>Trace Plots:</strong> Show MCMC chain paths. Red
                        region = burn-in. Chains should stabilize quickly.
                    </li>
                    <li>
                        <strong>Burn-in:</strong> Initial samples discarded
                        during MCMC warmup. These are kept separately from
                        posterior samples.
                    </li>
                    <li>
                        <strong>R̂ (Rhat) &lt; 1.01:</strong> ✓ Chains converged.
                        &gt;1.01 ⚠ needs more iterations.
                    </li>
                    <li>
                        <strong>Divergences:</strong> Points where gradient
                        estimate failed. Should be &lt;5%.
                    </li>
                </ul>
            </Alert>
        </div>
    );
}
