"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Container, Form, Button, Alert, Spinner, Card } from "react-bootstrap";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { API_ENDPOINTS } from "@/lib/constants";
import type { TokenResponse } from "@/types/api";

export default function RegisterPage() {
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();
    const { setUser } = useAuthStore();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);

        try {
            const response = await api.post<TokenResponse>(
                API_ENDPOINTS.AUTH.REGISTER,
                {
                    email,
                    password,
                    full_name: fullName,
                },
            );

            const {
                access_token,
                user_id,
                email: userEmail,
                full_name,
            } = response.data;
            setUser(
                {
                    user_id,
                    email: userEmail,
                    full_name,
                    is_active: true,
                    created_at: new Date().toISOString(),
                },
                access_token,
            );
            router.push("/upload");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Registration failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container className="d-flex align-items-center justify-content-center">
            <Card
                style={{ width: "100%", maxWidth: "400px" }}
                className="shadow-lg"
            >
                <Card.Body>
                    <h1 className="text-center mb-4 text-white">Register</h1>

                    {error && <Alert variant="danger">{error}</Alert>}

                    <Form onSubmit={handleSubmit}>
                        <Form.Group className="mb-3">
                            <Form.Label>Full Name</Form.Label>
                            <Form.Control
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                placeholder="John Doe"
                                disabled={loading}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Email</Form.Label>
                            <Form.Control
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="your@email.com"
                                disabled={loading}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Password</Form.Label>
                            <Form.Control
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                disabled={loading}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-4">
                            <Form.Label>Confirm Password</Form.Label>
                            <Form.Control
                                type="password"
                                value={confirmPassword}
                                onChange={(e) =>
                                    setConfirmPassword(e.target.value)
                                }
                                placeholder="••••••••"
                                disabled={loading}
                                required
                            />
                        </Form.Group>

                        <Button
                            variant="primary"
                            type="submit"
                            className="w-100 mb-3"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <Spinner
                                        animation="border"
                                        size="sm"
                                        className="me-2"
                                    />
                                    Registering...
                                </>
                            ) : (
                                "Register"
                            )}
                        </Button>
                    </Form>

                    <div className="text-center" style={{ color: "#ffffff" }}>
                        Already have an account?{" "}
                        <Link
                            href="/login"
                            className="text-decoration-none"
                            style={{
                                color: "var(--accent-cyan)",
                                fontWeight: "bold",
                            }}
                        >
                            Login here
                        </Link>
                    </div>
                </Card.Body>
            </Card>
        </Container>
    );
}
