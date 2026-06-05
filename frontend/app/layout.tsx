import type { Metadata } from "next";
import "bootstrap/dist/css/bootstrap.css";
import "./globals.css";
import { QueryProvider } from "@/lib/providers";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
    title: "Vendor Assessment Tool",
    description:
        "Advanced Bayesian Hierarchical Model for Vendor Performance Analysis",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body
                suppressHydrationWarning
                style={{
                    display: "flex",
                    flexDirection: "column",
                    minHeight: "100vh",
                }}
            >
                <QueryProvider>
                    <div
                        className="d-flex flex-column justify-content-between"
                        style={{ minHeight: "100vh" }}
                    >
                        <Navbar />
                        <main className="container-fluid">{children}</main>
                        <Footer />
                    </div>
                </QueryProvider>
            </body>
        </html>
    );
}
