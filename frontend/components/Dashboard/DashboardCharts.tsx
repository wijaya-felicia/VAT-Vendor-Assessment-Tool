"use client";

import { Row, Col, Spinner, Alert } from "react-bootstrap";
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    ScatterChart,
    Scatter,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";
import {
    usePriceTrends,
    usePerformanceMatrix,
    useDelayDistribution,
} from "@/hooks/useDashboard";

interface DashboardChartsProps {
    sessionId: string;
}

const ChartContainer = ({
    children,
    title,
}: {
    children: React.ReactNode;
    title: string;
}) => (
    <div className="chart-container">
        <h6 className="text-info mb-3">{title}</h6>
        {children}
    </div>
);

export default function DashboardCharts({ sessionId }: DashboardChartsProps) {
    const priceTrends = usePriceTrends(sessionId);
    const performanceMatrix = usePerformanceMatrix(sessionId);
    const delayDistribution = useDelayDistribution(sessionId);

    const isLoading =
        priceTrends.isLoading ||
        performanceMatrix.isLoading ||
        delayDistribution.isLoading;
    const hasError =
        priceTrends.error || performanceMatrix.error || delayDistribution.error;

    if (isLoading)
        return (
            <Spinner
                animation="border"
                variant="info"
                className="mx-auto d-block my-5"
            />
        );
    if (hasError) return <Alert variant="danger">Failed to load charts</Alert>;

    return (
        <div className="mt-5 pt-4">
            <h5 className="text-info mb-4">📊 Analytics</h5>

            <Row className="g-4">
                <Col lg={6}>
                    <ChartContainer title="💰 Price Trends by Vendor">
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={priceTrends.data || []}>
                                <CartesianGrid
                                    strokeDasharray="3 3"
                                    stroke="#3d424a"
                                />
                                <XAxis
                                    dataKey="vendor_name"
                                    tick={{ fill: "#a0a0a0", fontSize: 12 }}
                                />
                                <YAxis
                                    tick={{ fill: "#a0a0a0", fontSize: 12 }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: "#2d3139",
                                        border: "1px solid #3d424a",
                                        borderRadius: "8px",
                                    }}
                                    labelStyle={{ color: "#e0e0e0" }}
                                />
                                <Legend wrapperStyle={{ color: "#e0e0e0" }} />
                                <Bar
                                    dataKey="mean"
                                    fill="#0ea5e9"
                                    name="Mean Price Discrepancy %"
                                />
                                <Bar
                                    dataKey="min"
                                    fill="#10b981"
                                    name="Min"
                                    opacity={0.6}
                                />
                                <Bar
                                    dataKey="max"
                                    fill="#ef4444"
                                    name="Max"
                                    opacity={0.6}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </ChartContainer>
                </Col>

                <Col lg={6}>
                    <ChartContainer title="🎯 Vendor Performance Matrix">
                        <ResponsiveContainer width="100%" height={300}>
                            <ScatterChart
                                margin={{
                                    top: 20,
                                    right: 20,
                                    bottom: 20,
                                    left: 20,
                                }}
                            >
                                <CartesianGrid
                                    strokeDasharray="3 3"
                                    stroke="#3d424a"
                                />
                                <XAxis
                                    dataKey="price_accuracy"
                                    type="number"
                                    name="Price Accuracy Score"
                                    tick={{ fill: "#a0a0a0", fontSize: 12 }}
                                />
                                <YAxis
                                    dataKey="timeliness"
                                    type="number"
                                    name="Timeliness Score"
                                    tick={{ fill: "#a0a0a0", fontSize: 12 }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: "#2d3139",
                                        border: "1px solid #3d424a",
                                        borderRadius: "8px",
                                    }}
                                    labelStyle={{ color: "#e0e0e0" }}
                                    cursor={{ fill: "rgba(14, 165, 233, 0.1)" }}
                                />
                                <Scatter
                                    name="Vendors"
                                    data={performanceMatrix.data || []}
                                    fill="#0ea5e9"
                                />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </ChartContainer>
                </Col>

                <Col lg={12}>
                    <ChartContainer title="📦 Delivery Delay Distribution">
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={delayDistribution.data || []}>
                                <CartesianGrid
                                    strokeDasharray="3 3"
                                    stroke="#3d424a"
                                />
                                <XAxis
                                    dataKey="delay_days"
                                    tick={{ fill: "#a0a0a0", fontSize: 12 }}
                                />
                                <YAxis
                                    tick={{ fill: "#a0a0a0", fontSize: 12 }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: "#2d3139",
                                        border: "1px solid #3d424a",
                                        borderRadius: "8px",
                                    }}
                                    labelStyle={{ color: "#e0e0e0" }}
                                />
                                <Legend wrapperStyle={{ color: "#e0e0e0" }} />
                                <Bar
                                    dataKey="count"
                                    fill="#00d9ff"
                                    name="Number of Deliveries"
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </ChartContainer>
                </Col>
            </Row>
        </div>
    );
}
