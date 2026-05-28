"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Container, Row, Col, Alert, Spinner, Button } from "react-bootstrap";
import { useAuthStore } from "@/store/authStore";
import FileUpload from "@/components/Upload/FileUpload";
import MetricsCard from "@/components/Dashboard/MetricsCard";
import DashboardCharts from "@/components/Dashboard/DashboardCharts";
import type { UploadResponse } from "@/types/api";

export default function DashboardPage() {
    const { user, isLoading, checkAuth } = useAuthStore();
    const router = useRouter();
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push("/login");
        }
    }, [user, isLoading, router]);

    const handleUploadSuccess = (id: string, response: UploadResponse) => {
        setSessionId(id);
        setUploadData(response);
        setSuccess(
            `✓ Successfully uploaded ${response.row_count} transactions`,
        );
        setError("");

        // Auto-scroll to metrics
        setTimeout(() => {
            document
                .getElementById("metrics-section")
                ?.scrollIntoView({ behavior: "smooth" });
        }, 300);
    };

    const handleUploadError = (err: string) => {
        setError(err);
        setSuccess("");
    };

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
            <h1 className="page-title mb-2">📊 Dashboard</h1>
            <p className="text-light mb-4" style={{ color: "#ffffff" }}>
                Upload and analyze vendor performance data
            </p>

            {error && (
                <Alert
                    variant="danger"
                    onClose={() => setError("")}
                    dismissible
                >
                    {error}
                </Alert>
            )}
            {success && (
                <Alert
                    variant="success"
                    onClose={() => setSuccess("")}
                    dismissible
                >
                    {success}
                </Alert>
            )}

            <Row>
                <Col lg={8}>
                    <FileUpload
                        onSuccess={handleUploadSuccess}
                        onError={handleUploadError}
                    />
                </Col>
                <Col lg={4}>
                    <div className="card p-4">
                        <h6 className="text-info mb-3">💡 Tips</h6>
                        <ul
                            className="small text-light list-unstyled"
                            style={{ color: "#ffffff" }}
                        >
                            <li className="mb-2" style={{ color: "#ffffff" }}>
                                ✓ Ensure all three files are from the same
                                period
                            </li>
                            <li className="mb-2" style={{ color: "#ffffff" }}>
                                ✓ Check for duplicate records before uploading
                            </li>
                            <li className="mb-2" style={{ color: "#ffffff" }}>
                                ✓ Large files (&gt;10K rows) may take longer to
                                process
                            </li>
                            <li className="mb-2" style={{ color: "#ffffff" }}>
                                ✓ System performs automatic data validation
                            </li>
                        </ul>
                    </div>
                </Col>
            </Row>

            {sessionId && uploadData && (
                <>
                    <div id="metrics-section" className="mt-5 pt-4">
                        <MetricsCard sessionId={sessionId} />
                    </div>
                    <DashboardCharts sessionId={sessionId} />
                </>
            )}

            <div
                className="mt-5 pt-4"
                style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}
            >
                <Button
                    variant={sessionId && uploadData ? "info" : "secondary"}
                    disabled={!sessionId || !uploadData}
                    onClick={() => {
                        if (sessionId && uploadData) {
                            router.push("/rankings");
                        }
                    }}
                    size="lg"
                    style={{ minWidth: "200px" }}
                >
                    🏆 View Rankings
                </Button>
                <Button
                    variant={sessionId && uploadData ? "success" : "secondary"}
                    disabled={!sessionId || !uploadData}
                    onClick={() => {
                        if (sessionId && uploadData) {
                            router.push("/rankings");
                        }
                    }}
                    size="lg"
                    style={{ minWidth: "200px" }}
                >
                    🤖 Start BHM Modelling
                </Button>
            </div>
        </Container>
    );
}
