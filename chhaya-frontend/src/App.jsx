import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { LanguageProvider } from "./context/LanguageContext";
import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/auth/LoginPage";
import SignupPage from "./pages/auth/SignupPage";
import ReferenceSourcesListPage from "./pages/reference-sources/ReferenceSourcesListPage";
import AddSourcePage from "./pages/reference-sources/AddSourcePage";
import SourceDetailPage from "./pages/reference-sources/SourceDetailPage";
import StyleLibraryPage from "./pages/style-library/StyleLibraryPage";
import StudyGuidesListPage from "./pages/study-guides/StudyGuidesListPage";
import ConfigureGuidePage from "./pages/study-guides/ConfigureGuidePage";
import GuideDetailPage from "./pages/study-guides/GuideDetailPage";
import ExamPapersListPage from "./pages/exam-papers/ExamPapersListPage";
import UploadExamPaperPage from "./pages/exam-papers/UploadExamPaperPage";
import ExamPaperDetailPage from "./pages/exam-papers/ExamPaperDetailPage";
import AnalyticsDashboardPage from "./pages/progress/AnalyticsDashboardPage";
import ComingSoonPage from "./pages/ComingSoonPage";
import SessionTracker from "./components/SessionTracker";

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
      <LanguageProvider>
        <AuthProvider>
          {/* SessionTracker lives OUTSIDE <Routes> so React Router doesn't break,
              but INSIDE <AuthProvider> so it can read auth state.
              It mounts once per login and never re-mounts on page navigation. */}
          <SessionTracker />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />

            <Route path="/" element={<ProtectedRoute><AnalyticsDashboardPage /></ProtectedRoute>} />

            <Route path="/sources" element={<ProtectedRoute><ReferenceSourcesListPage /></ProtectedRoute>} />
            <Route path="/sources/new" element={<ProtectedRoute><AddSourcePage /></ProtectedRoute>} />
            <Route path="/sources/:id" element={<ProtectedRoute><SourceDetailPage /></ProtectedRoute>} />

            <Route path="/library" element={<ProtectedRoute><StyleLibraryPage /></ProtectedRoute>} />

            <Route path="/guides" element={<ProtectedRoute><StudyGuidesListPage /></ProtectedRoute>} />
            <Route path="/guides/new" element={<ProtectedRoute><ConfigureGuidePage /></ProtectedRoute>} />
            <Route path="/guides/:id" element={<ProtectedRoute><GuideDetailPage /></ProtectedRoute>} />

            <Route path="/exam-papers" element={<ProtectedRoute><ExamPapersListPage /></ProtectedRoute>} />
            <Route path="/exam-papers/new" element={<ProtectedRoute><UploadExamPaperPage /></ProtectedRoute>} />
            <Route path="/exam-papers/:id" element={<ProtectedRoute><ExamPaperDetailPage /></ProtectedRoute>} />

            <Route path="/concept-maps" element={<ProtectedRoute><ComingSoonPage title="Concept maps" /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><ComingSoonPage title="Settings" /></ProtectedRoute>} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}
