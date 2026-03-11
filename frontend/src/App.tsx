import { useEffect, useState } from "react";
import { Route, Routes, useLocation } from "react-router-dom";

import { ErrorBoundary } from "./components/ErrorBoundary";
import { OverviewPage } from "./pages/OverviewPage";
import { OperationsPage } from "./pages/OperationsPage";
import { ReviewsPage } from "./pages/ReviewsPage";
import { CompliancePage } from "./pages/CompliancePage";
import { JobPage } from "./pages/JobPage";
import { IntentPage } from "./pages/IntentPage";

export function App() {
  const location = useLocation();
  const [authExpired, setAuthExpired] = useState(false);

  useEffect(() => {
    document.title = `Converge UI · ${location.pathname}`;
  }, [location.pathname]);

  useEffect(() => {
    const handler = () => setAuthExpired(true);
    window.addEventListener("auth:expired", handler);
    return () => window.removeEventListener("auth:expired", handler);
  }, []);

  return (
    <>
      {authExpired && (
        <div role="alert" style={{
          background: "#fef3cd",
          color: "#856404",
          padding: "0.75rem 1rem",
          textAlign: "center",
          fontWeight: 500,
          borderBottom: "1px solid #ffc107",
        }}>
          Session expired. Please <button onClick={() => window.location.reload()} style={{
            background: "none",
            border: "none",
            color: "#0d6efd",
            cursor: "pointer",
            textDecoration: "underline",
            font: "inherit",
            fontWeight: 600,
            padding: 0,
          }}>refresh the page</button> to re-authenticate.
        </div>
      )}
      <Routes>
        <Route path="/" element={<ErrorBoundary pageName="Overview"><OverviewPage /></ErrorBoundary>} />
        <Route path="/operations" element={<ErrorBoundary pageName="Operations"><OperationsPage /></ErrorBoundary>} />
        <Route path="/reviews" element={<ErrorBoundary pageName="Reviews"><ReviewsPage /></ErrorBoundary>} />
        <Route path="/compliance" element={<ErrorBoundary pageName="Compliance"><CompliancePage /></ErrorBoundary>} />
        <Route path="/jobs/:jobId" element={<ErrorBoundary pageName="Job Detail"><JobPage /></ErrorBoundary>} />
        <Route path="/intents/:intentId" element={<ErrorBoundary pageName="Intent Detail"><IntentPage /></ErrorBoundary>} />
      </Routes>
    </>
  );
}
