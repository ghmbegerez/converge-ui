import { useEffect } from "react";
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

  useEffect(() => {
    document.title = `Converge UI · ${location.pathname}`;
  }, [location.pathname]);

  return (
    <Routes>
      <Route path="/" element={<ErrorBoundary pageName="Overview"><OverviewPage /></ErrorBoundary>} />
      <Route path="/operations" element={<ErrorBoundary pageName="Operations"><OperationsPage /></ErrorBoundary>} />
      <Route path="/reviews" element={<ErrorBoundary pageName="Reviews"><ReviewsPage /></ErrorBoundary>} />
      <Route path="/compliance" element={<ErrorBoundary pageName="Compliance"><CompliancePage /></ErrorBoundary>} />
      <Route path="/jobs/:jobId" element={<ErrorBoundary pageName="Job Detail"><JobPage /></ErrorBoundary>} />
      <Route path="/intents/:intentId" element={<ErrorBoundary pageName="Intent Detail"><IntentPage /></ErrorBoundary>} />
    </Routes>
  );
}
