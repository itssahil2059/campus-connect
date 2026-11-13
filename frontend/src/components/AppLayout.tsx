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
    `rounded-full px-2.5 py-1.5 text-sm transition sm:px-3 ${
      isActive ? "bg-sand font-medium text-ink" : "text-muted hover:text-ink"
    }`;

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-line bg-cream/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
          <Link to="/home" className="flex items-center gap-2 py-2 pr-2" aria-label="Home">
            <span className="h-2.5 w-2.5 rounded-full bg-accent" />
            <span className="hidden font-display text-lg font-semibold sm:inline">Git Together</span>
          </Link>

          <nav className="flex items-center gap-0.5 sm:gap-2">
            {/* On phones the logo is the Home link, to save space. */}
            <NavLink to="/home" className={(state) => `hidden sm:inline-block ${navClass(state)}`}>
              Home
            </NavLink>
            <NavLink to="/friends" className={navClass}>
              Friends
            </NavLink>
            <NavLink to="/messages" className={navClass}>
              Messages
            </NavLink>
            <NavLink to="/profile/edit" className={navClass}>
              Profile
            </NavLink>
            {user && (
              <div className="ml-1 hidden sm:block">
                <Avatar name={user.username} />
              </div>
            )}
            <button
              onClick={handleLogout}
              className="rounded-full px-2.5 py-1.5 text-sm text-muted transition hover:text-accent-dark sm:px-3"
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
