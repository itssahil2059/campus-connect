export default function Footer() {
  const team = [
    "Sahil Bhusal",
    "Christian Martinez",
    "Cezar Herrera",
    "Trinity Rodriguez",
  ];

  return (
    <footer className="relative border-t border-line">
      <div className="mx-auto max-w-5xl px-4 py-8 text-center sm:px-6">
        <p className="text-sm text-ink">
          (c) 2026 Git-Together - Capstone project
        </p>
        <p className="mt-2 text-sm text-muted">{team.join(" · ")}</p>
      </div>
    </footer>
  );
}