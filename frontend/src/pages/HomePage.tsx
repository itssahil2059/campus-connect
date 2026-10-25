import { Link } from "react-router-dom";
import Footer from "../components/Footer";

const steps = [
  {
    number: 1,
    title: "Verify your school email",
    text: "Sign up with your .edu address so everyone you meet is a real student.",
  },
  {
    number: 2,
    title: "Answer a short questionnaire",
    text: "Tell us about your interests and preferences in just a few minutes.",
  },
  {
    number: 3,
    title: "Discover, connect and chat",
    text: "Browse compatible students, add friends, and start a conversation.",
  },
];

const reasons = [
  {
    title: "Verified students only",
    text: "Every member signs up with a .edu email, so you know who you are talking to.",
  },
  {
    title: "Matches on shared interests, not just photos",
    text: "Our questionnaire pairs you with people who actually share your interests.",
  },
  {
    title: "Meet students from other colleges",
    text: "Find friends on your campus and at schools across the country.",
  },
];

// Same look as the shared Button in components/ui.tsx, but on Link elements.
const primaryLink =
  "inline-flex items-center justify-center rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-cream transition hover:bg-ink/85";
const outlineLink =
  "inline-flex items-center justify-center rounded-full border border-ink px-5 py-2.5 text-sm font-medium text-ink transition hover:bg-sand";
const ghostLink =
  "inline-flex items-center justify-center rounded-full px-5 py-2.5 text-sm font-medium text-ink transition hover:bg-sand";

// Same card look as the Login page card.
const card =
  "rounded-3xl border border-line bg-white/80 p-7 shadow-sm backdrop-blur";

export default function HomePage() {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden text-ink">
      {/* Soft background shapes (same as the Login page) */}
      <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-accent-soft blur-3xl" />
      <div className="pointer-events-none absolute -right-16 top-1/2 h-80 w-80 rounded-full bg-amber-100/70 blur-3xl" />

      {/* 1. Top bar */}
      <header className="relative border-b border-line">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-accent" />
            <span className="font-display text-xl font-semibold">
              Git-Together
            </span>
          </Link>
          <nav className="flex items-center gap-2">
            <Link to="/login" className={ghostLink}>
              Log in
            </Link>
            <Link to="/signup" className={primaryLink}>
              Sign up
            </Link>
          </nav>
        </div>
      </header>

      <main className="relative flex-1">
        {/* 2. Hero */}
        <section className="mx-auto max-w-3xl px-4 py-16 text-center sm:px-6 sm:py-24">
          <h1 className="font-display text-4xl font-semibold tracking-tight sm:text-5xl">
            Meet students who get you.
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-muted">
            Git-Together connects verified college students by shared interests,
            on your campus and beyond.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link to="/signup" className={`${primaryLink} w-full sm:w-auto`}>
              Sign up with your .edu email
            </Link>
            <Link to="/login" className={`${outlineLink} w-full sm:w-auto`}>
              Log in
            </Link>
          </div>
        </section>

        {/* 3. How it works */}
        <section className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
          <h2 className="text-center font-display text-3xl font-semibold">
            How it works
          </h2>
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {steps.map((step) => (
              <div key={step.number} className={card}>
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sand font-display font-semibold text-ink">
                  {step.number}
                </div>
                <h3 className="mt-4 font-display text-lg font-semibold">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm text-muted">{step.text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* 4. Why Git-Together */}
        <section className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
          <h2 className="text-center font-display text-3xl font-semibold">
            Why Git-Together
          </h2>
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {reasons.map((reason) => (
              <div key={reason.title} className={card}>
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent-soft font-semibold text-accent-dark">
                  ✓
                </div>
                <h3 className="mt-4 font-display text-lg font-semibold">
                  {reason.title}
                </h3>
                <p className="mt-2 text-sm text-muted">{reason.text}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* 5. Footer */}
      <Footer />
    </div>
  );
}