"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Container, Row, Col, Alert, Card, Button } from "react-bootstrap";
import FileUpload from "@/components/Upload/FileUpload";
import MetricsCard from "@/components/Dashboard/MetricsCard";
import DashboardCharts from "@/components/Dashboard/DashboardCharts";
import type { UploadResponse } from "@/types/api";

export default function PublicUploadPage() {
    const router = useRouter();
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

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

    return (
        <Container fluid>
            {/* Upload Section */}
            <Row>
                <Col lg={8} className="mx-auto">
                    <Card className="shadow-lg">
                        <Card.Header className="d-flex justify-content-between align-items-center">
                            <h4 className="mb-0">Upload Vendor Data</h4>
                        </Card.Header>
                        <Card.Body>
                            <p
                                className="text-light mb-4"
                                style={{ color: "#ffffff" }}
                            >
                                Upload three Excel files (PO, OC, SHIP) to
                                analyze vendor performance and get Bayesian
                                rankings.
                            </p>
                            <FileUpload
                                onSuccess={handleUploadSuccess}
                                onError={handleUploadError}
                            />
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
            {/* Messages */}
            {error && (
                <Row className="mb-4">
                    <Col lg={8} className="mx-auto">
                        <Alert
                            variant="danger"
                            onClose={() => setError("")}
                            dismissible
                        >
                            <strong>Upload Error:</strong> {error}
                        </Alert>
                    </Col>
                </Row>
            )}
            {success && (
                <Row className="mb-4">
                    <Col lg={8} className="mx-auto">
                        <Alert
                            variant="success"
                            onClose={() => setSuccess("")}
                            dismissible
                        >
                            {success}
                        </Alert>
                    </Col>
                </Row>
            )}
            {uploadData && sessionId && (
                <>
                    <div id="metrics-section" className="mb-5">
                        <Row className="mb-4">
                            <Col>
                                <h3 className="text-center mb-4 text-white">
                                    Analysis Results
                                </h3>
                            </Col>
                        </Row>
                        <Row>
                            <Col lg={10} className="mx-auto">
                                <MetricsCard sessionId={sessionId} />
                            </Col>
                        </Row>
                    </div>

                    {/* Charts Section */}
                    <Row className="mb-5">
                        <Col lg={12}>
                            <DashboardCharts sessionId={sessionId} />
                        </Col>
                    </Row>

                    {/* Navigation Buttons */}
                    <Row className="mb-5">
                        <Col lg={12} className="text-center">
                            <div
                                style={{
                                    display: "flex",
                                    gap: "1rem",
                                    justifyContent: "center",
                                    flexWrap: "wrap",
                                }}
                            >
                                <Button
                                    variant="success"
                                    size="lg"
                                    onClick={() =>
                                        router.push(
                                            `/rankings?session_id=${sessionId}`,
                                        )
                                    }
                                    style={{ minWidth: "200px" }}
                                >
                                    Start BHM Modelling
                                </Button>
                            </div>
                        </Col>
                    </Row>
                </>
            )}
            {/* Info Box */}
            {/* {!uploadData && (
                <Row className="mt-5">
                    <Col lg={8} className="mx-auto">
                        <Card className="bg-opacity-10">
                            <Card.Body>
                                <h5 style={{ color: "#ffffff" }}>
                                    What You'll Get:
                                </h5>
                                <ul
                                    className="mb-0"
                                    style={{ color: "#ffffff" }}
                                >
                                    <li>Transaction Analysis</li>
                                    <li>Vendor Performance Metrics</li>
                                    <li>Price & Timeliness Trends</li>
                                    <li>Bayesian Statistical Rankings</li>
                                    <li>Comparative Vendor Dashboard</li>
                                </ul>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            )} */}
        </Container>
    );
}
