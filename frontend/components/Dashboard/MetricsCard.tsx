"use client";

import { useDashboardMetrics } from "@/hooks/useDashboard";
import { Row, Col, Spinner, Alert } from "react-bootstrap";

interface MetricsCardProps {
    sessionId: string;
}

const MetricBox = ({
    label,
    value,
    unit = "",
}: {
    label: string;
    value: number | string;
    unit?: string;
}) => (
    <div className="metric-card">
        <div className="metric-label">{label}</div>
        <div className="metric-value">
            {typeof value === "number"
                ? value.toLocaleString("en-US", { maximumFractionDigits: 2 })
                : value}
            {unit && (
                <span className="ms-1" style={{ fontSize: "0.8em" }}>
                    {unit}
                </span>
            )}
        </div>
    </div>
);

export default function MetricsCard({ sessionId }: MetricsCardProps) {
    const { data, isLoading, error } = useDashboardMetrics(sessionId);

    if (isLoading)
        return (
            <Spinner
                animation="border"
                variant="info"
                className="mx-auto d-block"
            />
        );
    if (error) return <Alert variant="danger">Failed to load metrics</Alert>;
    if (!data) return null;

    return (
        <>
            <h5 className="text-info mb-4">📈 Key Metrics</h5>

            <Row className="g-3 mb-4">
                <Col md={6} lg={3}>
                    <MetricBox
                        label="Total Transactions"
                        value={data.total_transactions}
                    />
                </Col>
                <Col md={6} lg={3}>
                    <MetricBox
                        label="Total Spending"
                        value={data.total_spending}
                        unit="$"
                    />
                </Col>
                <Col md={6} lg={3}>
                    <MetricBox
                        label="Avg Transaction"
                        value={data.average_transaction_value}
                        unit="$"
                    />
                </Col>
                <Col md={6} lg={3}>
                    <MetricBox label="Vendors" value={data.vendor_count} />
                </Col>
            </Row>

            <Row className="g-3">
                <Col md={6} lg={3}>
                    <MetricBox
                        label="Avg Price Discrepancy"
                        value={data.price_discrepancy_mean}
                        unit="%"
                    />
                </Col>
                <Col md={6} lg={3}>
                    <MetricBox
                        label="Price Std Dev"
                        value={data.price_discrepancy_std}
                        unit="%"
                    />
                </Col>
                <Col md={6} lg={3}>
                    <MetricBox
                        label="Avg Delay"
                        value={data.delay_mean}
                        unit="days"
                    />
                </Col>
                <Col md={6} lg={3}>
                    <MetricBox
                        label="Delay Std Dev"
                        value={data.delay_std}
                        unit="days"
                    />
                </Col>
            </Row>

            <div className="mt-4 pt-3 border-top">
                <h6 className="text-info mb-4">📊 Vendor Summary</h6>
                <div className="table-responsive">
                    <table className="table table-sm table-striped">
                        <thead>
                            <tr>
                                <th>Vendor</th>
                                <th className="text-end">Transactions</th>
                                <th className="text-end">Avg Spending</th>
                                <th className="text-end">Price Disc.</th>
                                <th className="text-end">Delay</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.vendors.map((vendor) => (
                                <tr key={vendor.vendor_name}>
                                    <td className="fw-600">
                                        {vendor.vendor_name}
                                    </td>
                                    <td className="text-end small">
                                        {vendor.transaction_count}
                                    </td>
                                    <td className="text-end small">
                                        ${vendor.average_spending.toFixed(2)}
                                    </td>
                                    <td className="text-end small">
                                        {vendor.price_discrepancy_mean.toFixed(
                                            2,
                                        )}
                                        %
                                    </td>
                                    <td className="text-end small">
                                        {vendor.delay_mean.toFixed(2)}d
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </>
    );
}
