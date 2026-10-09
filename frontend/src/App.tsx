import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import AppLayout from "./components/AppLayout";
import RequireAuth from "./components/RequireAuth";
import HomePage from "./pages/HomePage";
import SignUpPage from "./pages/SignUpPage";
import LoginPage from "./pages/LoginPage";
import CheckEmailPage from "./pages/CheckEmailPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import FeedPage from "./pages/FeedPage";
import ProfileFormPage from "./pages/ProfileFormPage";
import QuestionnairePage from "./pages/QuestionnairePage";
import ProfileViewPage from "./pages/ProfileViewPage";
import DiscoverPage from "./pages/DiscoverPage";
import FriendsPage from "./pages/FriendsPage";
import MessagesPage from "./pages/MessagesPage";
import ChatPage from "./pages/ChatPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public pages. "/" is the landing page. */}
          <Route path="/" element={<HomePage />} />
          <Route path="/signup" element={<SignUpPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/check-email" element={<CheckEmailPage />} />
          <Route path="/verify/:uid/:token" element={<VerifyEmailPage />} />

          {/* Logged-in pages share the header layout. */}
          <Route
            element={
              <RequireAuth>
                <AppLayout />
              </RequireAuth>
            }
          >
            <Route path="/home" element={<FeedPage />} />
            <Route path="/profile/setup" element={<ProfileFormPage />} />
            <Route path="/profile/edit" element={<ProfileFormPage />} />
            <Route path="/profile/:id" element={<ProfileViewPage />} />
          </Route>

          {/* Placeholders for later features. */}
          <Route path="/questionnaire" element={<QuestionnairePage />} />
          <Route path="/discover" element={<DiscoverPage />} />
          <Route path="/friends" element={<FriendsPage />} />
          <Route path="/messages" element={<MessagesPage />} />
          <Route path="/messages/:id" element={<ChatPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
