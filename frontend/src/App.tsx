import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SignUpPage from "./pages/SignUpPage";
import LoginPage from "./pages/LoginPage";
import CheckEmailPage from "./pages/CheckEmailPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import ProfileFormPage from "./pages/ProfileFormPage";
import QuestionnairePage from "./pages/QuestionnairePage";
import ProfileViewPage from "./pages/ProfileViewPage";
import DiscoverPage from "./pages/DiscoverPage";
import FriendsPage from "./pages/FriendsPage";
import MessagesPage from "./pages/MessagesPage";
import ChatPage from "./pages/ChatPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/check-email" element={<CheckEmailPage />} />
        <Route path="/verify/:uid/:token" element={<VerifyEmailPage />} />
        <Route path="/profile/setup" element={<ProfileFormPage />} />
        <Route path="/profile/edit" element={<ProfileFormPage />} />
        <Route path="/questionnaire" element={<QuestionnairePage />} />
        <Route path="/profile/:id" element={<ProfileViewPage />} />
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/friends" element={<FriendsPage />} />
        <Route path="/messages" element={<MessagesPage />} />
        <Route path="/messages/:id" element={<ChatPage />} />
      </Routes>
    </BrowserRouter>
  );
}
