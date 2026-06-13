"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { Container, Row, Col, Spinner } from "react-bootstrap";
import Link from "next/link";

export default function HomePage() {
    const { user, isLoading, checkAuth } = useAuthStore();

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

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

    return (
        <Container
            fluid
            className="d-flex align-items-center justify-content-center"
            style={{ minHeight: "calc(100vh - 70px - 200px)" }}
        >
            <Container>
                <Row>
                    <Col lg={6}>
                        <h1 className="page-title">Vendor Assessment Tool</h1>
                        <p className="lead mb-4" style={{ color: "#b0d4ff" }}>
                            Advanced Bayesian Hierarchical Model for Vendor
                            Performance Analysis
                        </p>

                        <div className="mb-4">
                            {user ? (
                                <>
                                    <p
                                        style={{
                                            color: "#ffffff",
                                            fontSize: "1.1rem",
                                        }}
                                    >
                                        Welcome,{" "}
                                        <strong>
                                            {user.full_name || user.email}
                                        </strong>
                                        !
                                    </p>
                                    <p style={{ color: "#c8d6e5" }}>
                                        Ready to analyze vendor performance?
                                        Start by uploading your data.
                                    </p>
                                    <div className="d-flex gap-3">
                                        <Link
                                            href="/dashboard"
                                            className="btn btn-primary btn-lg"
                                        >
                                            Go to Dashboard
                                        </Link>
                                        <Link
                                            href="/rankings"
                                            className="btn btn-info btn-lg"
                                        >
                                            View Rankings
                                        </Link>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <p
                                        className="mb-4"
                                        style={{ color: "#c8d6e5" }}
                                    >
                                        This tool uses Bayesian statistics to
                                        evaluate vendor performance based on
                                        price accuracy and timeliness metrics.
                                    </p>
                                    <div className="d-flex gap-3 mb-4 flex-column flex-sm-row">
                                        <Link
                                            href="/upload"
                                            className="btn btn-success btn-lg flex-fill"
                                            style={{ background: "#10b981" }}
                                        >
                                            Upload Data Now!
                                        </Link>
                                        <Link
                                            href="/login"
                                            className="btn btn-primary btn-lg"
                                        >
                                            Login
                                        </Link>
                                        <Link
                                            href="/register"
                                            className="btn btn-outline-primary btn-lg"
                                        >
                                            Register
                                        </Link>
                                    </div>
                                    <div className="small text-white">
                                        <strong>Start Now:</strong> Click
                                        <em> "Upload Data Now"</em> to analyze
                                        vendor performance without creating an
                                        account. Or create an account to save
                                        your analysis history.
                                    </div>
                                </>
                            )}
                        </div>
                    </Col>

                    <Col lg={6}>
                        <div className="card p-4 mt-4 mt-lg-0">
                            <h5 className="text-info mb-4">
                                What you can do here:
                            </h5>
                            <ul className="list-unstyled">
                                <li className="mb-3">
                                    <span className="badge badge-primary">
                                        01
                                    </span>
                                    <span className="ms-2">
                                        Upload vendor data (PO, OC, Shipping
                                        Info)
                                    </span>
                                </li>
                                <li className="mb-3">
                                    <span className="badge badge-primary">
                                        02
                                    </span>
                                    <span className="ms-2">
                                        Automatic data merging and feature
                                        engineering
                                    </span>
                                </li>
                                <li className="mb-3">
                                    <span className="badge badge-primary">
                                        03
                                    </span>
                                    <span className="ms-2">
                                        Bayesian model fitting with MCMC
                                        Sampling
                                    </span>
                                </li>
                                <li className="mb-3">
                                    <span className="badge badge-primary">
                                        04
                                    </span>
                                    <span className="ms-2">
                                        Vendor rankings with confidence
                                        intervals
                                    </span>
                                </li>
                            </ul>
                            <div className="small text-white">
                                <strong>Best part?</strong> No login required to
                                upload and analyze your data! Just click{" "}
                                <em>"Upload Data Now"</em> and get insights in
                                minutes. Your data will not be saved after your
                                session ends.
                            </div>
                        </div>
                    </Col>
                </Row>
            </Container>
        </Container>
    );
}
