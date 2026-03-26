import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/rag", label: "RAG Chat" },
  { href: "/signals", label: "Signals" },
  { href: "/admin/ingest", label: "Admin Ingest" },
];

export function AppNav() {
  return (
    <header className="border-b border-zinc-200 bg-white">
      <nav className="mx-auto flex w-full max-w-6xl items-center gap-2 px-4 py-3">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="rounded-md px-3 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
