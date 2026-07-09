"use client";

import { useState, useRef } from "react";
import {
    Form,
    Button,
    Alert,
    Spinner,
    ProgressBar,
    ListGroup,
} from "react-bootstrap";
import { api } from "@/lib/api";
import { API_ENDPOINTS } from "@/lib/constants";
import type { UploadResponse } from "@/types/api";

interface FileUploadProps {
    onSuccess: (sessionId: string, response: UploadResponse) => void;
    onError: (error: string) => void;
}

export default function FileUpload({ onSuccess, onError }: FileUploadProps) {
    const [files, setFiles] = useState<{ po?: File; oc?: File; ship?: File }>(
        {},
    );
    const [loading, setLoading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const poInputRef = useRef<HTMLInputElement>(null);
    const ocInputRef = useRef<HTMLInputElement>(null);
    const shipInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange =
        (type: "po" | "oc" | "ship") =>
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0];
            if (file) {
                setFiles((prev) => ({ ...prev, [type]: file }));
            }
        };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!files.po || !files.oc || !files.ship) {
            onError("Please upload all three files (PO, OC, SHIP)");
            return;
        }

        setLoading(true);
        setUploadProgress(0);

        try {
            const formData = new FormData();
            formData.append("po", files.po);
            formData.append("oc", files.oc);
            formData.append("ship", files.ship);

            const progressInterval = setInterval(() => {
                setUploadProgress((prev) => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return prev;
                    }
                    return prev + 10;
                });
            }, 200);

            const response = await api.post<UploadResponse>(
                API_ENDPOINTS.UPLOAD,
                formData,
                {
                    headers: { "Content-Type": "multipart/form-data" },
                },
            );

            clearInterval(progressInterval);
            setUploadProgress(100);

            setFiles({});
            if (poInputRef.current) poInputRef.current.value = "";
            if (ocInputRef.current) ocInputRef.current.value = "";
            if (shipInputRef.current) shipInputRef.current.value = "";

            setTimeout(() => {
                onSuccess(response.data.session_id, response.data);
                setUploadProgress(0);
            }, 500);
        } catch (err: any) {
            let errorMessage = "Upload failed";

            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                if (Array.isArray(detail)) {
                    errorMessage = detail
                        .map((e: any) =>
                            typeof e === "string"
                                ? e
                                : e.msg || JSON.stringify(e),
                        )
                        .join("; ");
                } else if (typeof detail === "string") {
                    errorMessage = detail;
                } else if (typeof detail === "object" && detail.msg) {
                    errorMessage = detail.msg;
                } else {
                    errorMessage = JSON.stringify(detail);
                }
            } else if (err.message) {
                errorMessage = err.message;
            }

            onError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const isReady = files.po && files.oc && files.ship;

    return (
        <div className="card p-4 mb-4">
            <h5 className="mb-4 text-info">Upload Vendor Data Files</h5>

            <Form onSubmit={handleSubmit}>
                <div className="row mb-4">
                    <div className="col-md-4 mb-3 mb-md-0">
                        <Form.Group>
                            <Form.Label className="small text-light">
                                Purchase Order (PO)
                            </Form.Label>
                            <Form.Control
                                type="file"
                                accept=".xlsx,.xls"
                                onChange={handleFileChange("po")}
                                ref={poInputRef}
                                disabled={loading}
                                required
                            />
                            {files.po && (
                                <small className="text-success d-block mt-2">
                                    ✓ {files.po.name}
                                </small>
                            )}
                        </Form.Group>
                    </div>

                    <div className="col-md-4 mb-3 mb-md-0">
                        <Form.Group>
                            <Form.Label className="small text-light">
                                Order Confirmation (OC)
                            </Form.Label>
                            <Form.Control
                                type="file"
                                accept=".xlsx,.xls"
                                onChange={handleFileChange("oc")}
                                ref={ocInputRef}
                                disabled={loading}
                                required
                            />
                            {files.oc && (
                                <small className="text-success d-block mt-2">
                                    ✓ {files.oc.name}
                                </small>
                            )}
                        </Form.Group>
                    </div>

                    <div className="col-md-4">
                        <Form.Group>
                            <Form.Label className="small text-light">
                                Shipment (SHIP)
                            </Form.Label>
                            <Form.Control
                                type="file"
                                accept=".xlsx,.xls"
                                onChange={handleFileChange("ship")}
                                ref={shipInputRef}
                                disabled={loading}
                                required
                            />
                            {files.ship && (
                                <small className="text-success d-block mt-2">
                                    ✓ {files.ship.name}
                                </small>
                            )}
                        </Form.Group>
                    </div>
                </div>

                {uploadProgress > 0 && (
                    <div className="mb-3">
                        <ProgressBar
                            now={uploadProgress}
                            label={`${uploadProgress}%`}
                            animated
                        />
                    </div>
                )}

                <Button
                    variant="success"
                    type="submit"
                    disabled={!isReady || loading}
                    className="w-100"
                >
                    {loading ? (
                        <>
                            <Spinner
                                animation="border"
                                size="sm"
                                className="me-2"
                            />
                            Processing...
                        </>
                    ) : (
                        "Upload & Process"
                    )}
                </Button>
            </Form>

            <div className="mt-4 pt-2 border-top">
                <h6 className="text-light small">Required File Format</h6>
                <ListGroup variant="flush" className="small">
                    <ListGroup.Item className="bg-transparent border-0 text-light px-0">
                        • All files must be Excel (.xlsx)
                    </ListGroup.Item>
                    <ListGroup.Item className="bg-transparent border-0 text-light px-0">
                        • PO File must contain columns: date, po_number,
                        vendor_name, product_code, product_name, quantity,
                        price_per_unit, total_price.
                    </ListGroup.Item>
                    <ListGroup.Item className="bg-transparent border-0 text-light px-0">
                        • OC File must contain columns: date, po_number,
                        order_confirmation_number, product_code, quantity,
                        price_per_unit, total_price.
                    </ListGroup.Item>
                    <ListGroup.Item className="bg-transparent border-0 text-light px-0">
                        • SHIP File must contain columns: etd, po_number,
                        vendor_name.
                    </ListGroup.Item>
                    <ListGroup.Item className="bg-transparent border-0 text-light px-0">
                        • Date format should be consistent (YYYY-MM-DD
                        recommended)
                    </ListGroup.Item>
                </ListGroup>
            </div>
        </div>
    );
}
