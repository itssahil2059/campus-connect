import { Link } from "react-router-dom";
import Footer from "../components/Footer";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Top Bar */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="text-2xl font-bold text-blue-600"
          >
            Git-Together
          </Link>

          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="px-4 py-2 rounded-lg font-medium text-slate-700 hover:bg-slate-100"
            >
              Log in
            </Link>

            <Link
              to="/signup"
              className="px-4 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700"
            >
              Sign up
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main>
        <section className="px-6 py-20 sm:py-24 text-center">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-slate-800">
              Meet students who get you.
            </h1>

            <p className="mt-6 max-w-2xl mx-auto text-lg leading-8 text-slate-600">
              Git-Together connects verified college students by shared
              interests, on your campus and beyond.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row justify-center gap-4">
              <Link
                to="/signup"
                className="rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700"
              >
                Sign up with your .edu email
              </Link>

              <Link
                to="/login"
                className="rounded-xl border border-blue-600 bg-white px-6 py-3 font-semibold text-blue-600 hover:bg-blue-50"
              >
                Log in
              </Link>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="bg-white px-6 py-16">
          <div className="max-w-6xl mx-auto">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-slate-800">
                How it works
              </h2>

              <p className="mt-3 text-slate-600">
                Getting started with Git-Together is simple.
              </p>
            </div>

            <div className="mt-10 grid gap-6 md:grid-cols-3">
              <div className="bg-slate-50 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-bold">
                  1
                </div>

                <h3 className="mt-5 text-xl font-semibold">
                  Verify your school email
                </h3>

                <p className="mt-3 leading-7 text-slate-600">
                  Use your .edu email to verify that you are a college
                  student.
                </p>
              </div>

              <div className="bg-slate-50 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-bold">
                  2
                </div>

                <h3 className="mt-5 text-xl font-semibold">
                  Answer a short questionnaire
                </h3>

                <p className="mt-3 leading-7 text-slate-600">
                  Share your interests and preferences so Git-Together can
                  help find compatible students.
                </p>
              </div>

              <div className="bg-slate-50 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-bold">
                  3
                </div>

                <h3 className="mt-5 text-xl font-semibold">
                  Discover, connect and chat
                </h3>

                <p className="mt-3 leading-7 text-slate-600">
                  Discover students with shared interests, add friends, and
                  start conversations.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Why Git-Together */}
        <section className="px-6 py-16">
          <div className="max-w-6xl mx-auto">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-slate-800">
                Why Git-Together
              </h2>
            </div>

            <div className="mt-10 grid gap-6 md:grid-cols-3">
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h3 className="text-xl font-semibold">
                  Verified students only
                </h3>

                <p className="mt-3 leading-7 text-slate-600">
                  College email verification helps keep the community focused
                  on real college students.
                </p>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h3 className="text-xl font-semibold">
                  Matches on shared interests, not just photos
                </h3>

                <p className="mt-3 leading-7 text-slate-600">
                  Find students based on shared interests and preferences,
                  rather than appearance alone.
                </p>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h3 className="text-xl font-semibold">
                  Meet students from other colleges
                </h3>

                <p className="mt-3 leading-7 text-slate-600">
                  Connect with students from your campus and colleges beyond
                  your own.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}