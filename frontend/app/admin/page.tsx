"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
    Container,
    Row,
    Col,
    Form,
    Button,
    Alert,
    Spinner,
    Card,
} from "react-bootstrap";
import { useAuthStore } from "@/store/authStore";
import { useLockModel } from "@/hooks/useBHM";

export default function AdminPage() {
    const { user, isLoading, checkAuth } = useAuthStore();
    const router = useRouter();
    const [modelYear, setModelYear] = useState(
        new Date().getFullYear().toString(),
    );
    const [description, setDescription] = useState("");
    const [success, setSuccess] = useState("");
    const [error, setError] = useState("");

    const lockMutation = useLockModel();

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push("/login");
        }
    }, [user, isLoading, router]);

    const handleLockModel = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setSuccess("");

        try {
            await lockMutation.mutateAsync(modelYear);
            setSuccess(`✓ Model for ${modelYear} has been locked successfully`);
            setModelYear((parseInt(modelYear) + 1).toString());
            setDescription("");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to lock model");
        }
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
            <h1 className="page-title mb-2">⚙️ Admin Panel</h1>
            <p className="text-muted mb-4">
                Model management and configuration
            </p>

            <Row>
                <Col lg={6}>
                    <Card className="shadow-lg">
                        <Card.Body>
                            <h5 className="text-info mb-4">🔒 Lock Model</h5>

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

                            <Form onSubmit={handleLockModel}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Audit Year</Form.Label>
                                    <Form.Control
                                        type="number"
                                        min="2020"
                                        max="2099"
                                        value={modelYear}
                                        onChange={(e) =>
                                            setModelYear(e.target.value)
                                        }
                                        disabled={lockMutation.isPending}
                                        required
                                    />
                                    <Form.Text className="text-muted">
                                        Enter the audit year to lock (e.g.,
                                        2024)
                                    </Form.Text>
                                </Form.Group>

                                <Form.Group className="mb-4">
                                    <Form.Label>Description</Form.Label>
                                    <Form.Control
                                        as="textarea"
                                        rows={3}
                                        value={description}
                                        onChange={(e) =>
                                            setDescription(e.target.value)
                                        }
                                        placeholder="Optional notes about this audit..."
                                        disabled={lockMutation.isPending}
                                    />
                                </Form.Group>

                                <Button
                                    variant="primary"
                                    type="submit"
                                    className="w-100"
                                    disabled={lockMutation.isPending}
                                >
                                    {lockMutation.isPending ? (
                                        <>
                                            <Spinner
                                                animation="border"
                                                size="sm"
                                                className="me-2"
                                            />
                                            Locking...
                                        </>
                                    ) : (
                                        "🔒 Lock Model"
                                    )}
                                </Button>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>

                <Col lg={6}>
                    <Card>
                        <Card.Body>
                            <h5 className="text-info mb-3">
                                ℹ️ What is Model Locking?
                            </h5>
                            <p className="text-muted small mb-3">
                                Model locking saves the current posterior
                                distribution as a checkpoint for future Bayesian
                                updates.
                            </p>
                            <ul className="text-muted small list-unstyled">
                                <li className="mb-2">
                                    ✓ Locks the vendor rankings for the
                                    specified year
                                </li>
                                <li className="mb-2">
                                    ✓ Saves posterior distributions as priors
                                    for next year
                                </li>
                                <li className="mb-2">
                                    ✓ Enables year-over-year model comparison
                                </li>
                                <li className="mb-2">
                                    ✓ Prevents accidental overwriting of
                                    historical results
                                </li>
                            </ul>

                            <div className="alert alert-warning small mt-4 mb-0">
                                <strong>⚠️ Note:</strong> Locking is
                                irreversible. Make sure all data has been
                                validated before proceeding.
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Row className="mt-4">
                <Col>
                    <Card>
                        <Card.Body>
                            <h6 className="text-info mb-3">
                                📋 Configuration Status
                            </h6>
                            <table className="table table-sm mb-0">
                                <tbody>
                                    <tr>
                                        <td className="text-muted">
                                            Backend API
                                        </td>
                                        <td className="text-success">
                                            ✓ Connected
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="text-muted">Database</td>
                                        <td className="text-success">
                                            ✓ Active
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="text-muted">
                                            MCMC Engine
                                        </td>
                                        <td className="text-success">
                                            ✓ Ready
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="text-muted">
                                            Current User
                                        </td>
                                        <td>{user.email}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
}
