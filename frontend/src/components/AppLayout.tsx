import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Avatar } from "./ui";

/** Header + page container for logged-in pages. Child routes render in <Outlet />. */
export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-full px-3 py-1.5 text-sm transition ${
      isActive ? "bg-sand font-medium text-ink" : "text-muted hover:text-ink"
    }`;

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-line bg-cream/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
          <Link to="/home" className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-accent" />
            <span className="font-display text-lg font-semibold">Git Together</span>
          </Link>

          <nav className="flex items-center gap-1 sm:gap-2">
            <NavLink to="/home" className={navClass}>
              Home
            </NavLink>
            <NavLink to="/profile/edit" className={navClass}>
              My profile
            </NavLink>
            {user && (
              <div className="ml-1 hidden sm:block">
                <Avatar name={user.username} />
              </div>
            )}
            <button
              onClick={handleLogout}
              className="rounded-full px-3 py-1.5 text-sm text-muted transition hover:text-accent-dark"
            >
              Log out
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
        <Outlet />
      </main>
    </div>
  );
}
