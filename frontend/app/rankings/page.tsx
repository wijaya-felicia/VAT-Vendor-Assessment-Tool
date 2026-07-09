"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
    Container,
    Row,
    Col,
    Form,
    Alert,
    Spinner,
    Badge,
} from "react-bootstrap";
import Link from "next/link";
import { useAuthStore } from "@/store/authStore";
import { useBHMRankings } from "@/hooks/useBHM";
import { api } from "@/lib/api";
import MCMCDiagnostics from "@/components/BHM/MCMCDiagnostics";

export default function RankingsPage() {
    const { user, isLoading, checkAuth } = useAuthStore();
    const router = useRouter();
    const [sessionId, setSessionId] = useState("");
    const [fetchingSession, setFetchingSession] = useState(false);
    const [sortBy, setSortBy] = useState<"rank" | "price" | "timeliness">(
        "rank",
    );

    const {
        data: rankings,
        isLoading: ranksLoading,
        error: ranksError,
    } = useBHMRankings(sessionId || null);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const urlSessionId = params.get("session_id");
        if (urlSessionId) {
            setSessionId(urlSessionId);
        } else if (user && !sessionId) {
            setFetchingSession(true);
            api.get("/bhm/latest-session")
                .then((res) => {
                    setSessionId(res.data.session_id);
                    setFetchingSession(false);
                })
                .catch((err) => {
                    console.log("No previous uploads found");
                    setFetchingSession(false);
                });
        }
    }, [user, sessionId]);

    if (isLoading || fetchingSession) {
        return (
            <Container
                className="d-flex align-items-center justify-content-center"
                style={{ minHeight: "calc(100vh - 70px)" }}
            >
                <Spinner animation="border" variant="info" />
            </Container>
        );
    }

    if (!sessionId && !user) {
        return (
            <Container
                className="d-flex align-items-center justify-content-center"
                style={{ minHeight: "calc(100vh - 70px)" }}
            >
                <Alert variant="warning">
                    Please upload data first or{" "}
                    <Link href="/login">log in</Link> to view rankings.
                </Alert>
            </Container>
        );
    }

    const getRankBadgeClass = (rank: number) => {
        if (rank === 1) return "rank-1";
        if (rank === 2) return "rank-2";
        if (rank === 3) return "rank-3";
        return "rank-other";
    };

    const sortedRankings =
        rankings?.rankings?.slice().sort((a, b) => {
            if (sortBy === "rank") return a.rank - b.rank;
            if (sortBy === "price")
                return b.price_accuracy_score - a.price_accuracy_score;
            return b.timeliness_score - a.timeliness_score;
        }) || [];

    return (
        <Container className="py-4">
            <h1 className="page-title mb-2">Vendor Rankings</h1>
            <p className="text-light mb-4" style={{ color: "#ffffff" }}>
                Bayesian Hierarchical Model Results
            </p>

            <Row className="mb-4">
                <Col md={6}>
                    <Form.Group>
                        <Form.Label className="small">Session ID</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Enter session ID or leave blank for latest"
                            value={sessionId}
                            onChange={(e) => setSessionId(e.target.value)}
                        />
                    </Form.Group>
                </Col>
                <Col md={6}>
                    <Form.Group>
                        <Form.Label className="small">Sort By</Form.Label>
                        <Form.Select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value as any)}
                        >
                            <option value="rank">Overall Rank</option>
                            <option value="price">Price Accuracy</option>
                            <option value="timeliness">Timeliness</option>
                        </Form.Select>
                    </Form.Group>
                </Col>
            </Row>

            {ranksError && (
                <Alert variant="danger">
                    Failed to load rankings. Make sure you've uploaded data
                    first.
                </Alert>
            )}

            {ranksLoading ? (
                <Spinner
                    animation="border"
                    variant="info"
                    className="mx-auto d-block"
                />
            ) : rankings ? (
                <>
                    <Alert variant="info" className="small">
                        <strong>Model Status:</strong>{" "}
                        {rankings.convergence_status} |
                        <strong className="ms-2">MCMC Iterations:</strong>{" "}
                        {rankings.mcmc_iterations} |
                        <strong className="ms-2">Chains:</strong>{" "}
                        {rankings.mcmc_chains}
                        {rankings.convergence_warnings.length > 0 && (
                            <div className="mt-2">
                                {rankings.convergence_warnings.join(", ")}
                            </div>
                        )}
                    </Alert>

                    {sessionId && <MCMCDiagnostics sessionId={sessionId} />}

                    <div className="table-responsive">
                        <table className="table table-striped table-hover">
                            <thead>
                                <tr>
                                    <th
                                        className="text-center"
                                        style={{ width: "80px" }}
                                    >
                                        Rank
                                    </th>
                                    <th>Vendor</th>
                                    <th className="text-center">
                                        Transactions
                                    </th>
                                    <th className="text-end">Price Accuracy</th>
                                    <th className="text-end">Timeliness</th>
                                    <th className="text-end">Combined Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedRankings.map((vendor, index) => (
                                    <tr key={vendor.vendor_name}>
                                        <td className="text-center">
                                            <span
                                                className={`rank-badge ${getRankBadgeClass(index + 1)}`}
                                            >
                                                {index + 1}
                                            </span>
                                        </td>
                                        <td className="fw-600">
                                            {vendor.vendor_name}
                                        </td>
                                        <td className="text-center">
                                            {vendor.transaction_count}
                                        </td>
                                        <td className="text-end">
                                            <div>
                                                {vendor.price_accuracy_score.toFixed(
                                                    3,
                                                )}
                                            </div>
                                            <small className="text-muted">
                                                [
                                                {vendor.price_accuracy_ci_lower.toFixed(
                                                    3,
                                                )}
                                                ,{" "}
                                                {vendor.price_accuracy_ci_upper.toFixed(
                                                    3,
                                                )}
                                                ]
                                            </small>
                                        </td>
                                        <td className="text-end">
                                            <div>
                                                {vendor.timeliness_score.toFixed(
                                                    3,
                                                )}
                                            </div>
                                            <small className="text-muted">
                                                [
                                                {vendor.timeliness_ci_lower.toFixed(
                                                    3,
                                                )}
                                                ,{" "}
                                                {vendor.timeliness_ci_upper.toFixed(
                                                    3,
                                                )}
                                                ]
                                            </small>
                                        </td>
                                        <td className="text-end">
                                            <strong
                                                style={{ color: "#00d9ff" }}
                                            >
                                                {vendor.combined_rank_score.toFixed(
                                                    3,
                                                )}
                                            </strong>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            ) : (
                <Alert variant="warning">
                    No ranking data available. Upload data first in the
                    Dashboard.
                </Alert>
            )}
        </Container>
    );
}
