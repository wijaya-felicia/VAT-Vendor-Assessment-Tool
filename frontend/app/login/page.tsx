"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Container, Form, Button, Alert, Spinner, Card } from "react-bootstrap";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { API_ENDPOINTS } from "@/lib/constants";
import type { TokenResponse } from "@/types/api";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();
    const { setUser } = useAuthStore();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const response = await api.post<TokenResponse>(
                API_ENDPOINTS.AUTH.LOGIN,
                {
                    email,
                    password,
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
            router.push("/dashboard");
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                    "Login failed. Check credentials.",
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container
            className="d-flex align-items-center justify-content-center"
            style={{ minHeight: "calc(100vh - 70px)" }}
        >
            <Card
                style={{ width: "100%", maxWidth: "400px" }}
                className="shadow-lg"
            >
                <Card.Body>
                    <h1 className="text-center mb-4">
                        <span style={{ color: "var(--accent-cyan)" }}>⚡</span>{" "}
                        Login
                    </h1>

                    {error && <Alert variant="danger">{error}</Alert>}

                    <Form onSubmit={handleSubmit}>
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

                        <Form.Group className="mb-4">
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
                                    Logging in...
                                </>
                            ) : (
                                "Login"
                            )}
                        </Button>
                    </Form>

                    <div className="text-center" style={{ color: "#ffffff" }}>
                        Don't have an account?{" "}
                        <Link
                            href="/register"
                            className="text-decoration-none"
                            style={{
                                color: "var(--accent-cyan)",
                                fontWeight: "bold",
                            }}
                        >
                            Register here
                        </Link>
                    </div>
                </Card.Body>
            </Card>
        </Container>
    );
}
