"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Container, Row, Col, Spinner, Alert } from "react-bootstrap";
import Link from "next/link";
import { useAuthStore } from "@/store/authStore";
import { useBHMVendorDetail } from "@/hooks/useBHM";

interface VendorDetailPageProps {
    params: {
        vendor: string;
    };
}

export default function VendorDetailPage({ params }: VendorDetailPageProps) {
    const { user, isLoading, checkAuth } = useAuthStore();
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get("session_id");
    const vendorName = decodeURIComponent(params.vendor);

    const {
        data: detail,
        isLoading: detailLoading,
        error: detailError,
    } = useBHMVendorDetail(sessionId, vendorName);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push("/login");
        }
    }, [user, isLoading, router]);

    if (isLoading) {
        return (
            <Container
                className="d-flex align-items-center justify-content-center"
                style={{ minHeight: "calc(100vh - 70px)" }}
            >
                <Spinner animation="border" variant="info" />
            </Container>
        );
    }

    if (!user) return null;

    return (
        <Container className="py-4">
            <div className="mb-4">
                <Link
                    href="/rankings"
                    className="btn btn-outline-secondary btn-sm"
                >
                    ← Back to Rankings
                </Link>
            </div>

            {detailError && (
                <Alert variant="danger">Failed to load vendor details</Alert>
            )}

            {detailLoading ? (
                <Spinner
                    animation="border"
                    variant="info"
                    className="mx-auto d-block"
                />
            ) : detail ? (
                <>
                    <h1 className="page-title mb-1">
                        {detail.vendor_name}
                        <span className="ms-3" style={{ fontSize: "1.5rem" }}>
                            #{detail.rank}
                        </span>
                    </h1>
                    <p className="text-muted mb-4">
                        Detailed Performance Analysis
                    </p>

                    <Row className="g-4">
                        <Col lg={6}>
                            <div className="card p-4">
                                <h6 className="text-info mb-4">
                                    💰 Price Accuracy Score
                                </h6>
                                <div className="mb-3">
                                    <div className="mb-2">
                                        <strong
                                            style={{
                                                fontSize: "1.8rem",
                                                color: "#00d9ff",
                                            }}
                                        >
                                            {detail.price_accuracy_mean.toFixed(
                                                4,
                                            )}
                                        </strong>
                                    </div>
                                    <small className="text-muted">
                                        95% CI: [
                                        {detail.price_accuracy_ci_lower.toFixed(
                                            4,
                                        )}
                                        ,{" "}
                                        {detail.price_accuracy_ci_upper.toFixed(
                                            4,
                                        )}
                                        ]
                                    </small>
                                </div>
                                <div className="alert alert-info small">
                                    Higher values indicate better price accuracy
                                    (lower price discrepancies)
                                </div>
                            </div>
                        </Col>

                        <Col lg={6}>
                            <div className="card p-4">
                                <h6 className="text-info mb-4">
                                    ⏱️ Timeliness Score
                                </h6>
                                <div className="mb-3">
                                    <div className="mb-2">
                                        <strong
                                            style={{
                                                fontSize: "1.8rem",
                                                color: "#10b981",
                                            }}
                                        >
                                            {detail.timeliness_mean.toFixed(4)}
                                        </strong>
                                    </div>
                                    <small className="text-muted">
                                        95% CI: [
                                        {detail.timeliness_ci_lower.toFixed(4)},{" "}
                                        {detail.timeliness_ci_upper.toFixed(4)}]
                                    </small>
                                </div>
                                <div className="alert alert-success small">
                                    Higher values indicate better timeliness
                                    (shorter delivery delays)
                                </div>
                            </div>
                        </Col>
                    </Row>

                    <div className="card p-4 mt-4">
                        <h6 className="text-info mb-4">
                            📊 Overall Combined Score
                        </h6>
                        <div className="row">
                            <div className="col-md-6">
                                <div className="metric-card">
                                    <div className="metric-label">
                                        Combined Rank Score
                                    </div>
                                    <div
                                        className="metric-value"
                                        style={{ color: "#00d9ff" }}
                                    >
                                        {detail.combined_rank_score.toFixed(4)}
                                    </div>
                                </div>
                            </div>
                            <div className="col-md-6">
                                <div className="metric-card">
                                    <div className="metric-label">
                                        Confidence Level
                                    </div>
                                    <div
                                        className="metric-value"
                                        style={{ color: "#10b981" }}
                                    >
                                        {detail.confidence}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="card p-4 mt-4">
                        <h6 className="text-info mb-4">
                            🔍 Convergence Diagnostics
                        </h6>
                        <div className="table-responsive">
                            <table className="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Metric</th>
                                        <th className="text-center">
                                            R̂ (Rhat)
                                        </th>
                                        <th className="text-center">ESS</th>
                                        <th className="text-center">
                                            Divergences
                                        </th>
                                        <th className="text-center">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {detail.diagnostics.map((diag) => (
                                        <tr key={diag.metric_name}>
                                            <td className="fw-600">
                                                {diag.metric_name}
                                            </td>
                                            <td className="text-center">
                                                <span
                                                    className={
                                                        diag.r_hat < 1.01
                                                            ? "text-success"
                                                            : "text-danger"
                                                    }
                                                >
                                                    {diag.r_hat.toFixed(4)}
                                                </span>
                                            </td>
                                            <td className="text-center">
                                                {diag.effective_sample_size.toFixed(
                                                    0,
                                                )}
                                            </td>
                                            <td className="text-center">
                                                {diag.has_divergences ? (
                                                    <span className="badge bg-danger">
                                                        Yes
                                                    </span>
                                                ) : (
                                                    <span className="badge bg-success">
                                                        No
                                                    </span>
                                                )}
                                            </td>
                                            <td className="text-center">
                                                <span
                                                    className={`badge ${diag.rhat_status === "converged" ? "bg-success" : "bg-warning"}`}
                                                >
                                                    {diag.rhat_status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div className="card p-4 mt-4">
                        <h6 className="text-info mb-3">
                            📈 Summary Statistics
                        </h6>
                        <Row>
                            <div className="col-md-6">
                                <p>
                                    <strong>Total Transactions:</strong>{" "}
                                    {detail.transaction_count}
                                </p>
                            </div>
                        </Row>
                    </div>
                </>
            ) : (
                <Alert variant="warning">No vendor data available</Alert>
            )}
        </Container>
    );
}
