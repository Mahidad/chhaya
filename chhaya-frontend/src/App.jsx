import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/auth/LoginPage";
import SignupPage from "./pages/auth/SignupPage";
import ReferenceSourcesListPage from "./pages/reference-sources/ReferenceSourcesListPage";
import AddSourcePage from "./pages/reference-sources/AddSourcePage";
import SourceDetailPage from "./pages/reference-sources/SourceDetailPage";
import ComingSoonPage from "./pages/ComingSoonPage";

/*
  Route list mirrors the sidebar nav in components/layout/Sidebar.jsx.
  Only "Reference sources" has real pages behind it right now (Mahidad's
  Feature 1, the pilot module) -- everything else is a ComingSoonPage
  placeholder so the nav doesn't 404 while the rest of the team builds
  their modules on this same pattern.
*/
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          <Route path="/" element={<Navigate to="/sources" replace />} />

          <Route
            path="/sources"
            element={
              <ProtectedRoute>
                <ReferenceSourcesListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sources/new"
            element={
              <ProtectedRoute>
                <AddSourcePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sources/:id"
            element={
              <ProtectedRoute>
                <SourceDetailPage />
              </ProtectedRoute>
            }
          />

          <Route path="/library" element={<ProtectedRoute><ComingSoonPage title="Style library" /></ProtectedRoute>} />
          <Route path="/guides" element={<ProtectedRoute><ComingSoonPage title="Study guides" /></ProtectedRoute>} />
          <Route path="/concept-maps" element={<ProtectedRoute><ComingSoonPage title="Concept maps" /></ProtectedRoute>} />
          <Route path="/exams" element={<ProtectedRoute><ComingSoonPage title="Mock exams" /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><ComingSoonPage title="Settings" /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/sources" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
