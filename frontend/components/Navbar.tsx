"use client";

import { useAuthStore } from "@/store/authStore";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import {
    Navbar as BootstrapNavbar,
    Container,
    Nav,
    Button,
} from "react-bootstrap";

export default function Navbar() {
    const { user, logout, checkAuth } = useAuthStore();
    const router = useRouter();

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    const handleLogout = () => {
        logout();
        router.push("/login");
    };

    return (
        <BootstrapNavbar expand="lg" className="navbar">
            <Container fluid>
                <BootstrapNavbar.Brand as={Link} href="/">
                    VAT
                </BootstrapNavbar.Brand>
                <BootstrapNavbar.Toggle aria-controls="basic-navbar-nav" />
                <BootstrapNavbar.Collapse id="basic-navbar-nav">
                    <Nav className="ms-auto">
                        <Nav.Link as={Link} href="/upload">
                            Upload
                        </Nav.Link>
                        {user ? (
                            <>
                                <Nav.Link as={Link} href="/dashboard">
                                    Dashboard
                                </Nav.Link>
                                <Nav.Link as={Link} href="/rankings">
                                    Rankings
                                </Nav.Link>
                                <Nav.Link as={Link} href="/admin">
                                    Admin
                                </Nav.Link>
                                <div className="ms-3">
                                    <span className="text-light me-3">
                                        {user.email}
                                    </span>
                                    <Button
                                        variant="outline-light"
                                        size="sm"
                                        onClick={handleLogout}
                                    >
                                        Logout
                                    </Button>
                                </div>
                            </>
                        ) : (
                            <>
                                <Nav.Link as={Link} href="/login">
                                    Login
                                </Nav.Link>
                                <Nav.Link as={Link} href="/register">
                                    Register
                                </Nav.Link>
                            </>
                        )}
                    </Nav>
                </BootstrapNavbar.Collapse>
            </Container>
        </BootstrapNavbar>
    );
}
