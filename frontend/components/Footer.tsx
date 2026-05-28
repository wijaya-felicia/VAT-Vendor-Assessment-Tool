"use client";

import { Container, Row, Col } from "react-bootstrap";

export default function Footer() {
    return (
        <footer className="footer mt-auto py-4 bg-dark border-top">
            <Container>
                <Row>
                    <Col md={6} className="text-start text-muted small">
                        <p className="mb-0">
                            © 2026 Vendor Assessment Tool
                        </p>
                    </Col>
                    <Col md={6} className="text-end text-muted small">
                        <p className="mb-0">
                            Created by <strong>Felicia Angel Wijaya</strong> 2026
                        </p>
                    </Col>
                </Row>
            </Container>
        </footer>
    );
}
